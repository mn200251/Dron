package com.example.dronecontrol.services
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.app.NotificationCompat
import com.example.dronecontrol.R
import com.example.dronecontrol.data_types.InstructionType
import com.example.dronecontrol.exceptions.SocketException
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.INTERNAL
import com.example.dronecontrol.private.REPO_NAME
import com.example.dronecontrol.private.SERVER_FILE_PATH
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.utils.getCurrentIP
import com.example.dronecontrol.viewmodels.Controls
import com.example.dronecontrol.viewmodels.SCREEN
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.BufferedReader
import java.io.DataInputStream
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket


class ConnectionService : Service() {

    private val TIMEOUT_THIRD: Long = 1000
    private var socket: Socket? = null
    private var isInForeground = false
    private val serviceScope = CoroutineScope(Dispatchers.IO + Job())
    private var connectionActive: Boolean = false

    private var sendMovementJob: Job? = null
    private var receiveVideoStreamJob: Job? = null

    private var controls: Controls? = null

    var notification: Notification? = null

    private val channelId = "ConnectionService"
    private val notificationId = 1

    private val sendMovementDelay: Long = 50

    // private var isRecordingVideo = false
    // private var isRecordingInstructions = false

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onCreate() {
        super.onCreate()

        Log.d("SERVICE", "Usao u onCreate()")

        connect2Server(this)

    }

    // Method to update the notification based on the foreground status
    private fun updateNotification(isInForeground: Boolean, customTitle: String? = null, customText: String? = null) {
        var contentText = if (isInForeground && customText == null) {
            "The service is running in the foreground"
        } else {
            "The service is running in the background"
        }
        var contentTitle = customTitle ?: "Connected to Server"
        contentText = customText ?: contentText


        notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle(contentTitle)
            .setContentText(contentText)
            .setSmallIcon(R.drawable.connected_icon)
            .build()

        // Notify the NotificationManager to update the notification
        val notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(notificationId, notification)
    }

    private fun changeServiceState(toForeground: Boolean) {
        isInForeground = toForeground
        updateNotification(isInForeground)
    }

    private fun startForegroundService() {
        val channelId = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            createNotificationChannel(channelId, "ConnectionService")
        } else {
            "default"
        }

        notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle("Connected to Server")
            .setContentText("The service is running in the foreground")
            .setSmallIcon(R.drawable.connected_icon)
            .setPriority(NotificationCompat.BADGE_ICON_SMALL)
            .build()

        try {
            startForeground(notificationId, notification)
        }
        catch (e: SecurityException) {
            Log.d("SERVICE", e.toString())
        }

        isInForeground = true
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private fun createNotificationChannel(channelId: String, channelName: String): String {
        val channel = NotificationChannel(
            channelId,
            channelName,
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Channel description"
            enableLights(true)
            lightColor = Color.RED
            enableVibration(true)
        }

        val notificationManager: NotificationManager =
            getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannel(channel)

        return channelId
    }

    @RequiresApi(Build.VERSION_CODES.TIRAMISU)
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {

        Log.d("ConnectionServiceStart", "Usao u onStartCommand() sa: " + intent?.action)

        when (intent?.action) {
            "ACTION_APP_BACKGROUND" -> {
                if (connectionActive && isInForeground)
                    changeServiceState(false)
            }
            "ACTION_APP_FOREGROUND" -> {
                if (connectionActive && !isInForeground)
                    changeServiceState(true)

                val myData: Controls? = intent.getParcelableExtra("ControlData", Controls::class.java)
                if (myData != null)
                    controls = myData
            }

            InstructionType.START_RECORDING_VIDEO.value.toString() -> {
                val videoName = intent.getStringExtra("name")

                if (videoName != null) {
                    startRecordingVideo(videoName)
                }
            }

            InstructionType.STOP_RECORDING_VIDEO.value.toString() -> {
                stopRecordingVideo()
            }

            "ACTION_CONNECTION_NOT_ACTIVE" -> {
                connectionActive = false
            }

            InstructionType.TURN_ON.value.toString() -> {
                turnOn()
            }

            InstructionType.TURN_OFF.value.toString() -> {
                turnOff()
            }

            InstructionType.START_MACRO.value.toString() -> {
                val macroName = intent.getStringExtra("name")

                if (macroName != null) {
                    startMacro(macroName)
                }
            }

            InstructionType.START_RECORDING_MACRO.value.toString() -> {
                val macroName = intent.getStringExtra("name")

                if (macroName != null) {
                    startRecordingMacro(macroName)
                }
            }

            InstructionType.STOP_RECORDING_MACRO.value.toString() -> {
                stopRecordingMacro()
            }
        }

        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    private fun removeNotification(notificationId: Int)
    {
        val notificationManager = this.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.cancel(notificationId)
    }

    override fun onDestroy() {
        super.onDestroy()

        Log.d("SERVICE", "Usao u onDestroy()")

        val notificationManager = this.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.cancel(notificationId)

        sendMovementJob?.cancel()
        receiveVideoStreamJob?.cancel()

        socket?.close()
        connectionActive = false
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun connect2Server(service: Service)
    {
        serviceScope.launch(Dispatchers.IO)
        {
            var addressPair:Pair<String, String>?
            if(INTERNAL)
                addressPair=Pair("192.168.1.17", "6969")
            else
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)

            if (addressPair == null)
            {
                SharedRepository.setMainScreenErrorText("Unable to obtain server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)

            socket = Socket()
            val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())

            try{
                socket!!.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket!!.getOutputStream()
                val inputStream: InputStream = socket!!.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))

                try {
                    // authenticate user
                    val auth: String = "phone"
                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    var response = reader.readLine()
                    Log.d("Response", "Received response from server:$response")

                    startForegroundService()

                    if (response == "1") // drone not connected, wait?
                    {
                        response = reader.readLine()
                    }
                    if (response != "0") // an unknown error has occured
                    {
                        SharedRepository.setMainScreenErrorText("An unknown internal server error has occured!")
                        return@launch
                    }
                    // response == 0 - drone connected

                    getDroneStatus(reader)

                    SharedRepository.setMainScreenErrorText("")
                    SharedRepository.setScreen(SCREEN.DroneScreen)

                    connectionActive = true
                    socket!!.tcpNoDelay = true

                    sendMovementJob = serviceScope.launch(Dispatchers.Default)
                    {
                        sendMovement()
                    }

                    // called from thread that connects to server
                    receiveVideoStreamJob = serviceScope.launch(Dispatchers.Default)
                    {
                        receiveVideoStream()
                    }

                } catch (e: Exception) {
                    Log.d("Connection Exception - Inner Try", e.message.toString())
                    SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
                    removeNotification(notificationId)
                    service.stopSelf()
                } finally {

                }
            } catch (e: Exception) {
                Log.d("Connection Exception", e.message.toString())
                SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
                removeNotification(notificationId)
                service.stopSelf()
                // return@launch
            } finally {

            }
        }
    }

    private fun getDroneStatus(reader: BufferedReader)
    {
        var receivedByte = reader.readLine()
        val isPoweredOn = receivedByte == "1"
        SharedRepository.setPoweredOn(isPoweredOn)

        receivedByte = reader.readLine()
        val isRecordingVideo = receivedByte == "1"
        SharedRepository.setRecordingVideo(isRecordingVideo)

        receivedByte = reader.readLine()
        val isRecordingFlight = receivedByte == "1"
        SharedRepository.setRecordingMacro(isRecordingFlight)
    }

    @RequiresApi(Build.VERSION_CODES.O)
    suspend fun reconnect()
    {
        updateNotification(isInForeground, customTitle = "Lost connection",
            customText = "Trying to reconnnect to server...")

        SharedRepository.setMainScreenErrorText("Trying to reconnnect to server...")
        SharedRepository.setScreen(SCREEN.MainScreen)

        var addressPair:Pair<String, String>?
        if (INTERNAL){
            addressPair = Pair<String, String>("192.168.1.17", "6969")
        }else {
            addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)
        }
        if (addressPair == null)
        {
            SharedRepository.setMainScreenErrorText("Unable to obtain server IP!")
            return
        }

        Log.d("IP", addressPair.first + ":" + addressPair.second)

        val newSocket = Socket()
        // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
        val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())

        while (connectionActive && socket == null)
        {
            try{
                newSocket.connect(socketAddress, 2000)

                val outputStream: OutputStream = newSocket.getOutputStream()
                val inputStream: InputStream = newSocket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))

                try {
                    // authenticate user
                    val auth: String = "phone"
                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    var response = reader.readLine()
                    Log.d("Response", "Received response from server:$response")

                    startForegroundService()

                    if (response == "1") // drone not connected, wait?
                    {
                        response = reader.readLine()
                    }
                    if (response != "0") // an unknown error has occured
                    {
                        SharedRepository.setMainScreenErrorText("An unknown internal server error has occured!")
                        return
                    }

                    getDroneStatus(reader)

                    // reconnected successfully
                    socket = newSocket

                    SharedRepository.setMainScreenErrorText("")
                    SharedRepository.setScreen(SCREEN.DroneScreen)

                    socket!!.tcpNoDelay = true


                } catch (e: Exception) {
                    Log.d("Connection Exception - Inner Try", e.message.toString())
                    SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
                    removeNotification(notificationId)
                } finally {
                    delay(1) // used to stop thread if needed
                }
            } catch (e: Exception) {
                Log.d("Connection Exception", e.message.toString())
                SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
                removeNotification(notificationId)
                // return@launch
            } finally {
                delay(1) // used to stop thread if needed
            }
        }

        // if connection still active -> new socket, update notification
        if (connectionActive)
            updateNotification(isInForeground)
    }

    // called from thread that connects to server
    private suspend fun receiveVideoStream()
    {
        var inputStream: InputStream = socket!!.getInputStream()
        var dataInputStream = DataInputStream(inputStream)

//        var previousBitmap: Bitmap? = null

        val options = BitmapFactory.Options().apply {
            inPreferredConfig = Bitmap.Config.RGB_565 // Lower memory usage than ARGB_8888
        }

        while (connectionActive)
        {
            try {
                while (!isInForeground)
                {
                    delay(100)
                }

                if (socket == null)
                    throw SocketException("Socket is null!")

                val size: Int = dataInputStream.readInt()

                val jpegData = ByteArray(size)

                dataInputStream.readFully(jpegData)

                if (jpegData.size == size) {
                    val bitmap = BitmapFactory.decodeByteArray(jpegData, 0, size, options)

                    SharedRepository.setFrame(bitmap)
//
//                    previousBitmap?.recycle()
//                    previousBitmap = bitmap
                } else {
                    Log.e("DroneControl", "Incomplete frame received")
                }

//                val bitmap = BitmapFactory.decodeByteArray(jpegData, 0, size, options)
//
//                SharedRepository.setFrame(bitmap)


            }
            catch (e: CancellationException)
            {
                Log.e("ConnectionService VideoStream receiveVideoStream Exception", "CancellationException")
                return
            }
            catch (e: OutOfMemoryError)
            {
                Log.e("ConnectionService VideoStream receiveVideoStream Exception", "Out of memory error")
            }
            catch (e: Exception)
            {
                socket = null
                Log.e("ConnectionService VideoStream receiveVideoStream Exception", e.message.toString())
                inputStream.close()
                dataInputStream.close()

                // wait for control thread to make new socket
                while (socket == null)
                    delay(100)

                inputStream = socket!!.getInputStream()
                dataInputStream = DataInputStream(inputStream)
            }
            finally {

            }
        }
        inputStream.close()
        dataInputStream.close()

        Log.v("ConnectionService VideoStream", "Exited!")

        this.stopSelf()
    }

    private val instructionMap = mapOf("type" to InstructionType.HEARTBEAT.value)
    private fun heartbeat()
    {
        val jsonString = Json.encodeToString(instructionMap)

        sendJsonInstruction(InstructionType.HEARTBEAT.value)
    }

    /*
    // Start recording method
    private fun startInstructionRecording() {
        if (connectionActive && !SharedRepository.getRecordingMacro()) {
            SharedRepository.setRecordingMacro(true)

            sendJsonInstruction(InstructionType.RECORD_INST_START.value)
            Log.d("ConnectionService", "startInstructionRecording success")
        }
        else
        {
            Log.d("ConnectionService", "startInstructionRecording else branch conn = " + connectionActive.toString() +
                    ", recording flight = " + SharedRepository.getRecordingMacro().toString())
        }
    }

    // Stop recording method
    private fun stopInstructionRecording() {
        if (connectionActive && SharedRepository.getRecordingMacro()) {
            SharedRepository.setRecordingMacro(false)

            sendJsonInstruction(InstructionType.RECORD_INST_STOP.value)
            Log.d("ConnectionService", "stopInstructionRecording success")
        }
        else
        {
            Log.d("ConnectionService", "stopInstructionRecording else branch conn = " + connectionActive.toString() +
                    ", recording flight = " + SharedRepository.getRecordingMacro().toString())
        }
    }
    */


    private fun startRecordingVideo(videoName: String) {
        if (connectionActive) {
            serviceScope.launch {
                try {
                    val outputStream: OutputStream = socket!!.getOutputStream()

                    // Create an instance of Instruction with the given type and extras
                    val instruction = StartFlight(InstructionType.START_RECORDING_VIDEO.value, videoName)

                    // Serialize the instruction to JSON string
                    val jsonString = Json.encodeToString(instruction)

                    // Send the JSON string over the socket
                    outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    SharedRepository.setRecordingVideo(true)

                    Log.d("ConnectionService", "Sent JSON instruction: $jsonString")
                } catch (e: Exception) {
                    Log.e("ConnectionService", "Error sending JSON instruction: ${e.message}")
                }
            }
        }
    }

    private fun startMacro(macroName: String) {
        if (connectionActive) {
            serviceScope.launch {
                try {
                    val outputStream: OutputStream = socket!!.getOutputStream()

                    // Create an instance of Instruction with the given type and extras
                    val instruction = StartFlight(InstructionType.START_MACRO.value, macroName)

                    // Serialize the instruction to JSON string
                    val jsonString = Json.encodeToString(instruction)

                    // Send the JSON string over the socket
                    outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    Log.d("ConnectionService", "Sent JSON instruction: $jsonString")
                } catch (e: Exception) {
                    Log.e("ConnectionService", "Error sending JSON instruction: ${e.message}")
                }
            }
        }
    }

    // Stop recording method
    private fun stopRecordingVideo() {
        if (connectionActive) {
            SharedRepository.setRecordingVideo(false)

            sendJsonInstruction(InstructionType.STOP_RECORDING_VIDEO.value)
        }
    }

    private fun turnOn()
    {
        if (connectionActive) {
            SharedRepository.setPoweredOn(true)

            sendJsonInstruction(InstructionType.TURN_ON.value)
        }
    }

    private fun turnOff()
    {
        if (connectionActive ) {
            SharedRepository.setPoweredOn(false)

            sendJsonInstruction(InstructionType.TURN_OFF.value)
        }
    }

    @Serializable
    data class StartFlight(val type: Int, val name: String)

    private fun startRecordingMacro(macroName: String) {
        if (connectionActive) {

            serviceScope.launch {
                try {
                    val outputStream: OutputStream = socket!!.getOutputStream()

                    // Create an instance of Instruction with the given type and extras
                    val instruction = StartFlight(InstructionType.START_RECORDING_MACRO.value, macroName)

                    // Serialize the instruction to JSON string
                    val jsonString = Json.encodeToString(instruction)

                    // Send the JSON string over the socket
                    outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    SharedRepository.setRecordingMacro(true)

                    Log.d("ConnectionService", "Sent JSON instruction: $jsonString")
                }
                catch (e: Exception)
                {
                    Log.e("ConnectionService", "Error sending JSON instruction: ${e.message}")
                }
            }

            // sendJsonInstruction(InstructionType.START_FLIGHT.value)
        }
    }

    private fun stopRecordingMacro() {
        if (connectionActive ) {
            SharedRepository.setRecordingMacro(false)

            sendJsonInstruction(InstructionType.STOP_RECORDING_MACRO.value)
        }
    }

    // Method to send JSON instructions
    private fun sendJsonInstruction(type: Int) {
        serviceScope.launch {
            try {
                val outputStream: OutputStream = socket!!.getOutputStream()
                val jsonString = Json.encodeToString(mapOf("type" to type))
                outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
                outputStream.flush()
                //Log.e("ConnectionService", "Recording switch")
            } catch (e: Exception) {
                Log.e("ConnectionService", "Error sending JSON instruction: ${e}")
            }
        }
    }

    private fun sendControls(outputStream: OutputStream) {
        // Step 2: Serialize the data class instance to a JSON string
        val jsonString = Json.encodeToString(controls)

        outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
        outputStream.flush()

        controls = null
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private suspend fun sendMovement()
    {
        var outputStream: OutputStream = socket!!.getOutputStream()

        while(connectionActive)
        {
            try {
                if (socket == null)
                    throw SocketException("Socket is null!")

                if (controls != null)
                {
                    sendControls(outputStream)

                    delay(sendMovementDelay)
                }
                else
                {
                    while (controls == null)
                    {
                        if (socket == null)
                            throw SocketException("Socket is null!")

                        heartbeat()
                        delay(sendMovementDelay)
                    }
                }
            }
            catch (e: CancellationException)
            {
                Log.e("ConnectionService sendControls Exception", "CancellationException")
                return
            }
            catch (e: Exception)
            {
                socket = null
                Log.e("ConnectionService sendControls Exception", "Connection to server has been lost!")

                SharedRepository.setMainScreenErrorText("Connection to server has been lost!")
                SharedRepository.setScreen(SCREEN.MainScreen)

                outputStream.close()

                reconnect()
                outputStream = socket!!.getOutputStream()
            }
            finally {
                // outputStream.close()
            }
        }

        outputStream.close()
        Log.v("ConnectionService sendControls", "Exited!")
    }
}
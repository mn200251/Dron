package com.example.dronecontrol.services
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.Color
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.app.NotificationCompat
import com.example.dronecontrol.R
import com.example.dronecontrol.data_types.InstructionType
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.DOWNLOAD_FILE_PATH
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.REPO_NAME
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.utils.getCurrentIP
import com.example.dronecontrol.viewmodels.Controls
import com.example.dronecontrol.viewmodels.SCREEN
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
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

    private val internal=true

    private var isRecordingVideo = false

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onCreate() {
        super.onCreate()

        Log.d("SERVICE", "Usao u onCreate()")

        connect2Server(this)

    }

    // Method to update the notification based on the foreground status
    private fun updateNotification(isInForeground: Boolean) {
        val contentText = if (isInForeground) {
            "The service is running in the foreground"
        } else {
            "The service is running in the background"
        }

        notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle("Connected to Server")
            .setContentText(contentText)
            .setSmallIcon(R.drawable.connected_icon)
            .build()

        // Notify the NotificationManager to update the notification
        val notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(notificationId, notification)
    }

    // Example of changing the isInForeground value and updating the notification
    private fun changeServiceState(toForeground: Boolean) {
        isInForeground = toForeground
        updateNotification(isInForeground)
    }

    private fun startForegroundService() {
        val channelId = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            createNotificationChannel(channelId, "ConnectionService")
        } else {
            // If earlier version then do nothing and use a channel id from a predefined string
            "default"
        }

        notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle("Connected to Server")
            .setContentText("The service is running in the foreground")
            .setSmallIcon(R.drawable.connected_icon)
            .setPriority(NotificationCompat.BADGE_ICON_SMALL) // older versions use this to set priority
            .build()

        try {
            startForeground(notificationId, notification)
        }
        catch (e: SecurityException)
        {
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

        Log.d("SERVICE", "Usao u onStartCommand()")

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
            "ACTION_START_RECORDING" -> {
                startRecording()
            }
            "ACTION_STOP_RECORDING" -> {
                stopRecording()
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
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun connect2Server(service: Service)
    {
        serviceScope.launch(Dispatchers.IO)
        {
            var addressPair:Pair<String, String>?
            if(internal){
                addressPair=Pair<String, String>("192.168.1.17", "6969")
            }else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }
            if (addressPair == null)
            {
                SharedRepository.setMainScreenErrorText("Unable to obtain server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)

            socket = Socket()
            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
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

                    // start 1 thread for controls
                    SharedRepository.setMainScreenErrorText("")

                    SharedRepository.setScreen(SCREEN.DroneScreen)
                    connectionActive = true

                    socket!!.tcpNoDelay = true

                    sendMovementJob = serviceScope.launch(Dispatchers.Default)
                    {
                        sendMovement(socket!!)
                    }

                    // called from thread that connects to server
                    receiveVideoStreamJob = serviceScope.launch(Dispatchers.Default)
                    {
                        receiveVideoStream(socket!!)
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

    // called from thread that connects to server
    private suspend fun receiveVideoStream(socket: Socket)
    {
        val inputStream: InputStream = socket.getInputStream()
        val dataInputStream: DataInputStream = DataInputStream(inputStream)

        try {
            while (connectionActive)
            {
                while (!isInForeground)
                {
                    delay(100)
                }

                val size: Int = dataInputStream.readInt()

                // Read the JPEG data
                val jpegData = ByteArray(size)
                dataInputStream.readFully(jpegData)

                // Convert JPEG data to Bitmap
                val bitmap = BitmapFactory.decodeByteArray(jpegData, 0, size)

                SharedRepository.setFrame(bitmap)

//                val sizeBytes = ByteArray(4)
//                dataInputStream.readFully(sizeBytes)
//                val size = java.nio.ByteBuffer.wrap(sizeBytes).int
//
//                // Read the JPEG data
//                val jpegData = ByteArray(size)
//                dataInputStream.readFully(jpegData)
//
//                // Convert JPEG data to Bitmap
//                val bitmap = BitmapFactory.decodeByteArray(jpegData, 0, size)

            }
        }
        catch (e: Exception)
        {
            Log.e("ConnectionService VideoStream receiveVideoStream Exception", e.message.toString())


        }
        finally {
            inputStream.close()
        }

        Log.v("ConnectionService VideoStream", "Exited!")

        this.stopSelf()
    }

    private val instructionMap = mapOf("type" to InstructionType.HEARTBEAT.value)
    private fun heartbeat(outputStream: OutputStream)
    {
        val jsonString = Json.encodeToString(instructionMap)

        outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
        outputStream.flush()
    }

    // Start recording method
    private fun startRecording() {
        if (connectionActive && !isRecordingVideo) {
            isRecordingVideo = true
            sendJsonInstruction(InstructionType.START_RECORDING.value)
        }
    }

    // Stop recording method
    private fun stopRecording() {
        if (connectionActive && isRecordingVideo) {
            isRecordingVideo = false
            sendJsonInstruction(InstructionType.STOP_RECORDING.value)
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
                Log.e("ConnectionService", "Recording switch")
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

    private suspend fun sendMovement(socket: Socket)
    {
        val outputStream: OutputStream = socket.getOutputStream()
        // val coordinates = Coordinates(0f, 0f, 0f)

        try {
            while(connectionActive)
            {
                if (controls != null)
                {
                    sendControls(outputStream)

                    delay(100)
                }
                else
                {
                    delay(100)

                    while (controls == null)
                    {
                        heartbeat(outputStream)
                        delay(TIMEOUT_THIRD)
                    }
                }
            }
        }
        catch (e: Exception)
        {
            Log.e("ConnectionService sendControls Exception", e.message.toString())
        }
        finally {
            outputStream.close()
        }

        Log.v("ConnectionService sendControls", "Exited!")
    }
}
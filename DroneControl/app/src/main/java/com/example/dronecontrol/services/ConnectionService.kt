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
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.example.dronecontrol.R
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.FILE_PATH
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

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onCreate() {
        super.onCreate()

        Log.d("SERVICE", "Usao u onCreate()")

        connect2Server()

        /*
        if (!connectionActive)
        {
            this.stopSelf()
            return
        }
        */


        startForegroundService()
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
            .setContentText("The service is running in the background")
            .setSmallIcon(R.drawable.connected_icon)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT) // older versions use this to set priority
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
        /*
        val chan = NotificationChannel(channelId, channelName, NotificationManager.IMPORTANCE_DEFAULT)
        val service = getSystemService(NotificationManager::class.java)
        service?.createNotificationChannel(chan)
        return channelId

         */

        val channel = NotificationChannel(
            channelId,
            channelName,
            NotificationManager.IMPORTANCE_DEFAULT
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
                // Switch to heartbeat mode
                // startHeartbeat()
                changeServiceState(false)
            }
            "ACTION_APP_FOREGROUND" -> {
                changeServiceState(true)

                val myData: Controls? = intent.getParcelableExtra("ControlData", Controls::class.java)
                if (myData != null)
                {
                    controls = myData
                }
            }
        }

        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        super.onDestroy()

        Log.d("SERVICE", "Usao u onDestroy()")

        sendMovementJob?.cancel()
        receiveVideoStreamJob?.cancel()

        socket?.close()
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun connect2Server()
    {
        serviceScope.launch(Dispatchers.Default)
        {
            val addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, FILE_PATH, BRANCH_NAME)

            if (addressPair == null)
            {
                SharedRepository.setMainScreenErrorText("Unable to obtain server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)



            var socket = Socket()
            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
            val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())

            try{
                socket.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket.getOutputStream()
                val inputStream: InputStream = socket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))

                try {
                    // authenticate user
                    val auth: String = "phone"
                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    var response = BufferedReader(InputStreamReader(socket.inputStream)).readLine()
                    Log.d("Response", "Received response from server:$response")

                    if (response == "1") // drone not connected, wait?
                    {
                        response = BufferedReader(InputStreamReader(socket.inputStream)).readLine()
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

                    socket.tcpNoDelay = true

                    sendMovementJob = serviceScope.launch(Dispatchers.Default)
                    {
                        sendMovement(socket)
                    }

                    // called from thread that connects to server
                    receiveVideoStreamJob = serviceScope.launch(Dispatchers.Default)
                    {
                        receiveVideoStream(socket)
                    }

                } catch (e: Exception) {

                } finally {

                }
            } catch (e: Exception) {
                Log.d("Connection Exception", e.message.toString())
                SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
                return@launch
            } finally {
                // connectionActive will be false
                // updateScreen(SCREEN.MainScreen)

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
                    delay(50)
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
            Log.e("VideoStream Exception", e.message.toString())
        }
        finally {
            inputStream.close()
        }

        Log.v("VideoStream", "Exited!")

        this.stopSelf()
    }

    private fun heartbeat(outputStream: OutputStream)
    {
        val jsonString = Json.encodeToString("ping")

        outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
        outputStream.flush()
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
                        delay(200)
                    }
                }
            }
        }
        catch (e: Exception)
        {
            Log.e("Controls Exception", e.message.toString())
        }
        finally {
            outputStream.close()
        }

        Log.v("Controls", "Exited!")
    }
}
package com.example.dronecontrol.services

import android.Manifest
import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.os.Message
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.example.dronecontrol.R
import com.example.dronecontrol.data_types.InstructionType
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.DOWNLOAD_FILE_PATH
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.INTERNAL
import com.example.dronecontrol.private.REPO_NAME
import com.example.dronecontrol.private.SERVER_FILE_PATH
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.utils.getCurrentIP
import com.fasterxml.jackson.databind.JsonSerializer.None
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONException
import org.json.JSONObject
import java.io.BufferedReader
import java.io.DataInputStream
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.nio.ByteBuffer
import java.nio.ByteOrder


class DownloadService : Service()
{
    private var downloadJob: Job? = null
    private val serviceScope = CoroutineScope(Dispatchers.IO + Job())

    private val channelId = "DownloadService"
    private val notificationId = 2

    private val errorChannelId = "ErrorDownloadService"
    private val errorNotificationId = 3

    private var serviceDownloading = false

    private val WIDTH=1920  //prebaci na sta god da su dimenzije pi snimka
    private val HEIGHT = 1080
    private val FRAME_RATE= 30

    private val byteToSend:Byte=1

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onCreate() {
        super.onCreate()

        createNotificationChannel(channelId, channelId, "Download Channel")
        createNotificationChannel(errorChannelId, errorChannelId, "Download Channel")
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun downloadVideo(service: Service, videoName: String) {
        serviceDownloading = true
        // Check and request storage permission if not granted
//        if (ContextCompat.checkSelfPermission(service, Manifest.permission.WRITE_EXTERNAL_STORAGE)
//            != PackageManager.PERMISSION_GRANTED) {
//
//            // Request WRITE_EXTERNAL_STORAGE permission
//            ActivityCompat.requestPermissions(
//                service as Activity,
//                arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE),
//                1
//            )
//            return
//        }

        downloadJob = serviceScope.launch(Dispatchers.IO)
        {
            // startForegroundService("The service is downloading your video")
            updateNotification(
                notificationId, channelId, "Downloading Video",
                "Video is transfering to device", R.drawable.download_icon, oneTime = false, 0, 100
            )
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair<String, String>("192.168.1.17", "6969")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)
            }

            if (addressPair == null) {
                // SharedRepository.setMainScreenErrorText("Unable to obtain download server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)

            // Define the output video file
            val outputDir = getExternalFilesDir(null)
            val outputFile = File(outputDir, videoName)


            var auth: String = "phone"
            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
            val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())
            var socket: Socket? = null
            var status = false
            try {
                socket = Socket()
                // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
                val socketAddress =
                    InetSocketAddress(addressPair.first, addressPair.second.toInt())

                socket.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket.getOutputStream()
                val inputStream: InputStream = socket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))
                val dataInputStream = DataInputStream(socket.getInputStream())
                outputStream.write(auth.toByteArray(Charsets.UTF_8))
                outputStream.flush()
                var response1 = BufferedReader(InputStreamReader(inputStream)).readLine()

                val json = JSONObject().apply {
                    put("type", InstructionType.DOWNLOAD_VIDEO.value)
                    put("video_name", videoName)
                }
                outputStream.write(json.toString().toByteArray(Charsets.UTF_8))
            } catch (e: Exception) {
                Log.d("DownloadService", "Download failed to start: ${e.message}")
                service.stopSelf()
                return@launch
            } finally {
                socket?.close()
            }
            delay(1000)
            var progress = 0
            var jsonResponse: JSONObject? = null
            auth = "video_download"
            while (true) {
                delay(3000)
                try {
                    socket = Socket()
                    //socket.soTimeout=3000
                    // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
                    val socketAddress =
                        InetSocketAddress(addressPair.first, addressPair.second.toInt())

                    socket.connect(socketAddress, 2000)

                    val outputStream: OutputStream = socket.getOutputStream()

                    val reader = BufferedReader(InputStreamReader( socket.getInputStream()))
                    val inputStream = DataInputStream(socket.getInputStream())

                    //start communication
                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
                    outputStream.flush()
                    var response = BufferedReader(InputStreamReader(inputStream)).readLine()

                    //wait for upload on server to finish
                    var json = JSONObject().apply {
                        put("type", InstructionType.GET_STATUS.value)
                    }
                    while (!status) {
                        outputStream.write(json.toString().toByteArray(Charsets.UTF_8))
                        val status_str = reader.readLine()
                        if (status_str.equals("ok")) {
                            status = true
                        } else{
                            delay(1000)
                        }
                        Log.d("DownloadService", status_str)
                    }
                    updateNotification(
                        notificationId, channelId, "Video upload finished",
                        "Starting the link handling.", R.drawable.download_successs, oneTime = true
                    )
                    //get the link
                    var jsonResponse: JSONObject? = null
                    json = JSONObject().apply {
                        put("type", InstructionType.GET_LINK.value)
                    }
                    // Loop until we successfully receive and parse the JSON data
                    while (jsonResponse == null) {
                        try {
                            outputStream.write(json.toString().toByteArray(Charsets.UTF_8))
                            // Get the input stream to read from the socket
                            val inputStream = socket.getInputStream()
                            val reader = BufferedReader(InputStreamReader(inputStream))

                            val jsonDataString =reader.readLine() ?: throw Exception("No data received")
                            Log.d("DownloadService", jsonDataString)
                            jsonResponse = JSONObject(jsonDataString)
                            break

                        } catch (e: JSONException) {
                            // Handle the exception (you can log it, or just retry)
                            Log.d("DownloadService", e.toString())
                        }
                    }
                    //use the link
                    // If status is success, get the download URL
                    val fileUrl = jsonResponse!!.getString("link")

                    // Pass the URL to the browser to handle the download
                    openUrlInBrowser(service, fileUrl)

                    // Notify user that the download has been passed to the browser
                    updateNotification(
                        notificationId,
                        channelId,
                        "Downloading in Browser",
                        "The video is being downloaded in your browser.",
                        R.drawable.download_successs,
                        oneTime = true
                    )
                    break
                } catch (e: Exception) {
                    Log.d("DownloadService", "Working on uploading the video: " + e)
                    updateNotification(
                        notificationId, channelId, "Downloading Video",
                        "Working on uploading the video", R.drawable.download_icon, oneTime = false
                    )
                } finally {
                    socket?.close()
                }
            }
            service.stopSelf()
            return@launch
        }
    }

    private fun openUrlInBrowser(context: Context, url: String) {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            data = Uri.parse(url)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK // Start the activity from the service
        }
        context.startActivity(intent)
    }

    private fun updateNotification(notifId: Int, chanId: String, title: String, message: String,
                                   icon: Int, oneTime: Boolean, progress: Int = 0, maxProgress: Int = 100)
    {
        val notif = NotificationCompat.Builder(this, chanId)
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(icon)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        // Notify the NotificationManager to update the notification
        val notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        // notificationManager.notify(notificationId, notification)

        // if the notification can be swiped or not
        if (oneTime)
            notificationManager.notify(notifId, notif)
        else
            startForeground(notifId, notif)
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private fun createNotificationChannel(channelId: String, channelName: String, desc: String): String {
        val channel = NotificationChannel(
            channelId,
            channelName,
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = desc
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
        if (serviceDownloading && intent?.getStringExtra("videoName") != null)
        {
            updateNotification(errorNotificationId, errorChannelId, "Error Downloading Video",
               "Already downloading video from server!", R.drawable.download_failed, oneTime = true)
            return START_STICKY
        }


        when (intent?.action) {
            "ACTION_APP_BACKGROUND" -> {

            }

            "ACTION_APP_FOREGROUND" -> {

            }
        }

        val videoName = intent?.getStringExtra("videoName")
        if (videoName != null)
        {
            downloadVideo(this, videoName)
        }
        else
            this.stopSelf()

        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()

        downloadJob?.cancel()
        val notificationManager = this.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.cancel(errorNotificationId)
        // notificationManager.cancel(notificationId)
    }


    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

}
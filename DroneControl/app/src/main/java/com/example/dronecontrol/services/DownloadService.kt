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

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onCreate() {
        super.onCreate()

        createNotificationChannel(channelId, channelId, "Download Channel")
        createNotificationChannel(errorChannelId, errorChannelId, "Download Channel")
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun downloadVideo(service: Service, videoName: String) {
        serviceDownloading = true

        downloadJob = serviceScope.launch(Dispatchers.IO)
        {
            // startForegroundService("The service is downloading your video")
            updateNotification(
                notificationId, channelId, "Downloading Video",
                "Video is transfering to device", R.drawable.download_icon, oneTime = false, 0, 100
            )
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair("192.168.1.17", "42069")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }

            if (addressPair == null) {
                return@launch
            }

            var auth: String = "phone"
            var socket: Socket? = null
            var status = false

            delay(1000)
            var first=true
            auth = "video_download"
            while (true) {
                delay(3000)
                try {
                    socket = Socket()
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
                    if(first){
                        val json = JSONObject().apply {
                            put("type", InstructionType.DOWNLOAD_VIDEO.value)
                            put("video_name", videoName)
                        }
                        outputStream.write(json.toString().toByteArray(Charsets.UTF_8))
                        outputStream.flush()

                        first=false
                        delay(1000)
                    }
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

                    val fileUrl = jsonResponse!!.getString("link")

                    openUrlInBrowser(service, fileUrl)

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
package com.example.dronecontrol.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import android.os.Build
import android.os.IBinder
import android.os.Message
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
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.io.BufferedReader
import java.io.DataInputStream
import java.io.File
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket


class DownloadService : Service()
{
    private var downloadJob: Job? = null
    private val serviceScope = CoroutineScope(Dispatchers.IO + Job())

    private val channelId = "DownloadService"
    private val notificationId = 2

    private val errorChannelId = "ErrorDownloadService"
    private val errorNotificationId = 3

    private var serviceDownloading = false

    private val internal=true

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
//            // startForegroundService("The service is downloading your video")
//            updateNotification(notificationId, channelId, "Downloading Video",
//                "Video is downloading to device", R.drawable.download_icon,oneTime = false,0,100)
//            var addressPair:Pair<String, String>?
//            if(internal){
//                addressPair=Pair<String, String>("192.168.1.17", "6969")
//            }else {
//                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
//            }
//
//            if (addressPair == null) {
//                // SharedRepository.setMainScreenErrorText("Unable to obtain download server IP!")
//                return@launch
//            }
//
//            Log.d("IP", addressPair.first + ":" + addressPair.second)
//
//
//            var socket = Socket()
//            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
//            val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())
//
//            try {
//                socket.connect(socketAddress, 2000)
//
//                val outputStream: OutputStream = socket.getOutputStream()
//                val inputStream: InputStream = socket.getInputStream()
//                val reader = BufferedReader(InputStreamReader(inputStream))
//                val dataInputStream = DataInputStream(socket.getInputStream())
//
//                var currFrame = 0
//                try {
//                      // authenticate user
////                    val auth: String = "phone"
////                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
////                    outputStream.flush()
//                    val auth: String = "phone"
//                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
//                    val json = JSONObject().apply {
//                        put("type", InstructionType.DOWNLOAD_VIDEO.value)
//                        put("video_name", videoName)
//                    }
//                    outputStream.write(json.toString().toByteArray(Charsets.UTF_8))
//
//                    // Define the output video file
//                    val outputDir = getExternalFilesDir(null)
//                    val outputFile = File(outputDir, "${videoName}_received.mp4")
//
//                    // Setup MediaMuxer for video writing
//                    val mediaMuxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
//
//                    // Set up MediaCodec for encoding video
//                    val videoEncoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
//                    val mediaFormat = MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, 1280, 720)
//                    mediaFormat.setInteger(MediaFormat.KEY_BIT_RATE, 4000000) // Adjust bitrate for quality
//                    mediaFormat.setInteger(MediaFormat.KEY_FRAME_RATE, 60) // 60 fps
//                    mediaFormat.setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatYUV420Flexible)
//                    mediaFormat.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 5)
//                    videoEncoder.configure(mediaFormat, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
//                    videoEncoder.start()
//
//                    var numFrames = dataInputStream.readInt()
//
//
//                    // MediaMuxer track index
//                    var videoTrackIndex = -1
//                    val progressIncrement = 100 / numFrames
//
//                    while (currFrame < numFrames) {
//                        val frameSize = dataInputStream.readInt()
//                        val frameData = ByteArray(frameSize)
//                        dataInputStream.readFully(frameData)
//
//                        // Process the frameData to fit MediaCodec's input format
//                        val bufferInfo = MediaCodec.BufferInfo()
//                        val inputBufferIndex = videoEncoder.dequeueInputBuffer(10000)
//                        if (inputBufferIndex >= 0) {
//                            val inputBuffer = videoEncoder.getInputBuffer(inputBufferIndex)
//                            inputBuffer?.clear()
//                            inputBuffer?.put(frameData)
//                            videoEncoder.queueInputBuffer(inputBufferIndex, 0, frameSize, 0, 0)
//                        }
//
//                        var outputBufferIndex = videoEncoder.dequeueOutputBuffer(bufferInfo, 10000)
//                        while (outputBufferIndex >= 0) {
//                            val outputBuffer = videoEncoder.getOutputBuffer(outputBufferIndex)
//                            outputBuffer?.let {
//                                if (videoTrackIndex == -1) {
//                                    val format = videoEncoder.outputFormat
//                                    videoTrackIndex = mediaMuxer.addTrack(format)
//                                    mediaMuxer.start()
//                                }
//                                mediaMuxer.writeSampleData(videoTrackIndex, it, bufferInfo)
//                            }
//                            videoEncoder.releaseOutputBuffer(outputBufferIndex, false)
//                            outputBufferIndex = videoEncoder.dequeueOutputBuffer(bufferInfo, 10000)
//                        }
//
//                        currFrame++
//                        // Update notification progress
//                        val progress = currFrame * progressIncrement
//                        updateNotification(notificationId, channelId, "Downloading Video",
//                            "Video is downloading to device", R.drawable.download_icon, oneTime = false, progress = progress, maxProgress = 100)
//
//                    }
//
//                    mediaMuxer.stop()
//                    mediaMuxer.release()
//                    videoEncoder.stop()
//                    videoEncoder.release()
//
//                } catch (e: Exception) {
//
//                    Log.d("download"," "+currFrame+"died cause: "+e)
//                } finally {
//
//                }
//                updateNotification(notificationId, channelId, "Finished Downloading Video",
//                    "Video saved to device", R.drawable.download_successs,oneTime = true,100)
//
//            } catch (e: Exception) {
//                Log.d("DOWNLOAD SERVICE EXCEPTION", e.message.toString())
//                // SharedRepository.setMainScreenErrorText("An error has occurred while connecting to the server!")
//
//                updateNotification(notificationId, channelId, "Error Downloading Video",
//                    "An unexpected error has occured", R.drawable.download_failed, oneTime = true)
//
//                service.stopSelf()
//
//                return@launch
//            } finally {
//                // connectionActive will be false
//                // updateScreen(SCREEN.MainScreen)
//
//                serviceDownloading = false
//            }
        }
    }

    private fun updateNotification(notifId: Int, chanId: String, title: String, message: String,
                                   icon: Int, oneTime: Boolean, progress: Int = 0, maxProgress: Int = 100)
    {
        val notif = NotificationCompat.Builder(this, chanId)
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(icon)
            .setPriority(NotificationCompat.PRIORITY_HIGH) // older versions use this to set priority
            .setProgress(maxProgress, progress, false)
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
//            if (errorNotification != null)
//            {
//                // cancel error notification is active
//                val notificationManager = this.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
//                notificationManager.cancel(errorNotificationId)
//                errorNotification = null
//            }

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
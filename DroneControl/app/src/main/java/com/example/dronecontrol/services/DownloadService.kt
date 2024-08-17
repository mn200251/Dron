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

    private val internal=true

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

        downloadJob = serviceScope.launch(Dispatchers.IO)
        {
            // startForegroundService("The service is downloading your video")
            updateNotification(notificationId, channelId, "Downloading Video",
                "Video is downloading to device", R.drawable.download_icon,oneTime = false,0,100)
            var addressPair:Pair<String, String>?
            if(internal){
                addressPair=Pair<String, String>("192.168.1.17", "6969")
            }else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }

            if (addressPair == null) {
                // SharedRepository.setMainScreenErrorText("Unable to obtain download server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)

            // Define the output video file
            val outputDir = getExternalFilesDir(null)
            val outputFile = File(outputDir, "${videoName}_received.mp4")

            // Setup MediaMuxer for video writing
            val mediaMuxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)

            // Set up MediaCodec for encoding video
            val videoEncoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
            val mediaFormat = MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, WIDTH, HEIGHT)
            mediaFormat.setInteger(MediaFormat.KEY_BIT_RATE, 4000000) // Adjust bitrate for quality
            mediaFormat.setInteger(MediaFormat.KEY_FRAME_RATE, FRAME_RATE) // 60 fps
            mediaFormat.setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatYUV420Flexible)
            mediaFormat.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 5)
            videoEncoder.configure(mediaFormat, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            videoEncoder.start()

            var socket :Socket?=null
            var working=true
            var currFrame = 0
            var videoTrackIndex = -1
            var progressIncrement:Double = 1.0
            var numFrames =0
            val auth: String = "phone"
            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
            val socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())
            while(working) {
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
                    var response = BufferedReader(InputStreamReader(inputStream)).readLine()

                    //start the download only the first time
                        if(currFrame==0) {
                            val json = JSONObject().apply {
                                put("type", InstructionType.DOWNLOAD_VIDEO.value)
                                put("video_name", videoName)
                            }
                            outputStream.write(json.toString().toByteArray(Charsets.UTF_8))

                            val frameSizeBytes = ByteArray(4)
                            dataInputStream.readFully(frameSizeBytes)
                            numFrames =
                                ByteBuffer.wrap(frameSizeBytes).order(ByteOrder.BIG_ENDIAN).int
                            Log.d("DownloadService", "Parsed frame number: $numFrames")


                            progressIncrement = 100.0 / numFrames
                        }
                        //receive frames and create a video
                        while (currFrame < numFrames) {
                            val frameSize = dataInputStream.readInt()
                            val frameData = ByteArray(frameSize)
                            dataInputStream.readFully(frameData)

                            // Process the frameData to fit MediaCodec's input format
                            val bufferInfo = MediaCodec.BufferInfo()
                            val inputBufferIndex = videoEncoder.dequeueInputBuffer(10000)
                            if (inputBufferIndex >= 0) {
                                val inputBuffer = videoEncoder.getInputBuffer(inputBufferIndex)
                                inputBuffer?.clear()
                                inputBuffer?.put(frameData)
                                videoEncoder.queueInputBuffer(inputBufferIndex, 0, frameSize, 0, 0)
                            }

                            var outputBufferIndex =
                                videoEncoder.dequeueOutputBuffer(bufferInfo, 10000)
                            while (outputBufferIndex >= 0) {
                                val outputBuffer = videoEncoder.getOutputBuffer(outputBufferIndex)
                                outputBuffer?.let {
                                    if (videoTrackIndex == -1) {
                                        val format = videoEncoder.outputFormat
                                        videoTrackIndex = mediaMuxer.addTrack(format)
                                        mediaMuxer.start()
                                    }
                                    mediaMuxer.writeSampleData(videoTrackIndex, it, bufferInfo)
                                }
                                videoEncoder.releaseOutputBuffer(outputBufferIndex, false)
                                outputBufferIndex =
                                    videoEncoder.dequeueOutputBuffer(bufferInfo, 10000)
                            }

                            currFrame++
                            if (currFrame==numFrames){
                                working=false
                            }
                            if (currFrame % 4 == 0) {
                                Log.d("DownloadService", "Parsed frame: $currFrame")
                                outputStream.write(byteToSend.toInt())
                                outputStream.flush()
                                // Update notification progress
                                updateNotification(
                                    notificationId,
                                    channelId,
                                    "Downloading Video",
                                    "Video is downloading to device",
                                    R.drawable.download_icon,
                                    oneTime = false,
                                    progress = (currFrame * progressIncrement).toInt(),
                                    maxProgress = 100
                                )

                            }

                        }
                }  catch (e: Exception) {
                    Log.d("download", "at " + currFrame + " restarted cause: " + e)
                    //the server finished sending and the download cannot be recovered
                    //so just skip the last few frames
                    if(currFrame>numFrames-4){
                        working=false
                    }

                } finally {
                    socket?.close()
                    serviceDownloading = false
                }
            }
            try {
                mediaMuxer.stop()
                mediaMuxer.release()
                videoEncoder.stop()
                videoEncoder.release()
            } catch (e: Exception) {
                Log.d("DownloadService", " saving failed :  " + e)
            }
            Log.d("DownloadService", "Finished downloading the video")

            updateNotification(
                notificationId, channelId, "Finished Downloading Video",
                "Video saved to device", R.drawable.download_successs, oneTime = true, 100
            )
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
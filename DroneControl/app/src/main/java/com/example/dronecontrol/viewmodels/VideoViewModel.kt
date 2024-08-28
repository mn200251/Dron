package com.example.dronecontrol.viewmodels

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.os.Parcelable
import android.util.Base64
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.DataInputStream
import java.io.DataOutputStream
import java.net.Socket
import org.json.JSONObject
import androidx.lifecycle.SavedStateHandle
import com.example.dronecontrol.data_types.InstructionType
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.DOWNLOAD_FILE_PATH
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.INTERNAL
import com.example.dronecontrol.private.REPO_NAME
import com.example.dronecontrol.private.SERVER_FILE_PATH
import com.example.dronecontrol.utils.getCurrentIP
import kotlinx.parcelize.Parcelize
import org.json.JSONArray
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.InetSocketAddress

@Parcelize
data class Video(
    val filename: String,
    val thumbnail: Bitmap? // You can change this to a Bitmap if preferred
): Parcelable

@Parcelize
data class VideoState(
    val videos: List<Video> = emptyList()
) : Parcelable

const val VIDEO_STATE_KEY = "videoState"

class VideoViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel()  {

    private val _videoState = savedStateHandle.getStateFlow(VIDEO_STATE_KEY, VideoState())

    val videoState = _videoState


    @RequiresApi(Build.VERSION_CODES.O)
    fun fetchVideos() {
        viewModelScope.launch(Dispatchers.IO) {
            var socket: Socket? = null
            var auth: String = "phone"
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair<String, String>("192.168.1.17", "6970")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)
            }
            val socketAddress = addressPair?.second?.let {
                InetSocketAddress(
                    addressPair?.first,
                    it.toInt()
                )
            }
            var numberOfVideos = 0

            val videos = mutableListOf<Video>()
            var cnt = -1
            auth = "video_listing"
            while (cnt < numberOfVideos) {
                try {
                    socket = Socket()
                    socket.connect(socketAddress, 2000)
                    val videoOutputStream = DataOutputStream(socket.getOutputStream())
                    val videoInputStream = DataInputStream(socket.getInputStream())

                    // Re-authenticate for the new connection
                    videoOutputStream.write(auth.toByteArray(Charsets.UTF_8))
                    videoOutputStream.flush()
                    val videoResponse =BufferedReader(InputStreamReader(videoInputStream)).readLine()

                    //if first contact get the length of the list
                    if(cnt==-1){
                        //Send a request to get videos
                        val request = JSONObject().apply {
                            put("type", InstructionType.GET_VIDEOS.value)
                        }
                        videoOutputStream.writeUTF(request.toString())
                        videoOutputStream.flush()
                        val reader = BufferedReader(InputStreamReader( socket.getInputStream()))
                        numberOfVideos = reader.readLine().toInt()
                        Log.d("VideoViewModel", "Number of videos: $numberOfVideos")
                        cnt=0
                    }



                    // Request the next video
                    while(cnt < numberOfVideos) {
                        val videoRequest = JSONObject().apply {
                            put("type", InstructionType.GET_VIDEOS.value)
                            put("index",cnt)
                        }
                        videoOutputStream.writeUTF(videoRequest.toString())

                        // Read the length of the response
                        val length = videoInputStream.readInt()
                        Log.d("VideoViewModel", "Length: $length")
                        val responseData = ByteArray(length)
                        videoInputStream.readFully(responseData)

                        // Parse the received video JSON data
                        val responseJsonString = String(responseData, Charsets.UTF_8)
                        val videoJson = JSONObject(responseJsonString)

                        val filename = videoJson.getString("filename")
                        val thumbnail =
                            Base64.decode(
                                videoJson.getString("thumbnail").toByteArray(),
                                Base64.DEFAULT
                            )
                        val thumbnailBitmap =
                            BitmapFactory.decodeByteArray(thumbnail, 0, thumbnail.size)

                        // Add the video to the list
                        videos.add(Video(filename, thumbnailBitmap))
                        val updatedVideos = videos.toMutableList()
                        savedStateHandle[VIDEO_STATE_KEY] = VideoState(updatedVideos)
                        cnt++
                    }
                } catch (e: Exception) {
                    // Handle exceptions and retry logic if necessary
                    Log.d("VideoViewModel", "Error receiving video ${cnt}: ${e.message}")
                } finally {
                    socket?.close()
                }
            }
            Log.d("VideoViewModel", "Finished receiving video list")

        }
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun fetchVideosOld() {
        viewModelScope.launch(Dispatchers.IO) {
            var socket = Socket()
            var socketAddress:InetSocketAddress

            if(INTERNAL){
                socketAddress = InetSocketAddress("192.168.1.17", 6969)
            }else {
                val addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)
                socketAddress = InetSocketAddress(addressPair?.first, addressPair?.second!!.toInt())
            }


            try {
                socket.connect(socketAddress, 2000)
                val outputStream = DataOutputStream(socket.getOutputStream())
                val inputStream = DataInputStream(socket.getInputStream())

                val auth: String = "phone"
                outputStream.write(auth.toByteArray(Charsets.UTF_8))
                outputStream.flush()

                var response = BufferedReader(InputStreamReader(inputStream)).readLine()


                // Send request to get videos
                val request = JSONObject().apply {
                    put("type", InstructionType.GET_VIDEOS.value)
                }
                outputStream.writeUTF(request.toString())

                // Read the length of the response
                val length = inputStream.readInt()
                Log.d("VideoViewModel", "Response length: $length")
                // Read the response data
                val responseData = ByteArray(length)
                inputStream.readFully(responseData)

                // Parse the response JSON
                val responseJsonString = String(responseData, Charsets.UTF_8)
                val videoArray = JSONArray(responseJsonString)
                val videos = mutableListOf<Video>()

                for (i in 0 until videoArray.length()) {
                    val videoJson = videoArray.getJSONObject(i)
                    val filename = videoJson.getString("filename")
                    val thumbnail = Base64.decode(videoJson.getString("thumbnail").toByteArray(), Base64.DEFAULT) // You may need to decode this if it's encoded in Base64 or another format
                    val thumbnailBitmap = BitmapFactory.decodeByteArray(thumbnail, 0, thumbnail.size)
                    videos.add(Video(filename, thumbnailBitmap ))
                }

                // Update the video list in the state
                val newState = VideoState(videos)
                savedStateHandle[VIDEO_STATE_KEY] = newState

            } catch (e: Exception) {

                e.printStackTrace()
            } finally {
                socket.close()
            }
        }
    }

    fun downloadVideo(video: Video) {
        Log.d("Dialog","Yes")
    }
}

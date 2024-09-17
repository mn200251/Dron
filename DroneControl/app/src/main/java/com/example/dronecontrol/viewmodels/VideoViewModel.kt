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
import com.example.dronecontrol.utils.getCurrentIP
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.parcelize.Parcelize
import org.json.JSONArray
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.InetSocketAddress

@Parcelize
data class Video(
    var filename: String,
    val thumbnail: Bitmap? // You can change this to a Bitmap if preferred
): Parcelable

@Parcelize
data class VideoState(
    var videos: List<Video> = emptyList(),
    var isLoading: Boolean = false,
    var refresh: Boolean = true
) : Parcelable

const val VIDEO_STATE_KEY = "videoState"

class VideoViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel()  {

    private val _videoState1 = MutableStateFlow(VideoState())

    private val _videoState2 = savedStateHandle.getStateFlow(VIDEO_STATE_KEY, VideoState())

    val videoState = _videoState2


    @RequiresApi(Build.VERSION_CODES.O)
    fun fetchVideos(wait: Long? = null) {
        viewModelScope.launch(Dispatchers.IO) {
            setIsLoading(true)

            // wait is used to sleep the thread so that
            // the server can rename/delete the video in time
            if (wait != null)
                delay(wait)

            var socket: Socket? = null
            var auth: String = "phone"
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair<String, String>("192.168.1.17", "42069")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }
            val socketAddress = addressPair?.second?.let {
                InetSocketAddress(
                    addressPair.first,
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
                        // savedStateHandle[VIDEO_STATE_KEY] = VideoState(videos = updatedVideos)
                        setVideos(updatedVideos)
                        cnt++
                    }
                } catch (e: Exception) {
                    // Handle exceptions and retry logic if necessary
                    Log.d("VideoViewModel", "Error receiving video ${cnt}: ${e.message}")
                } finally {
                    socket?.close()

                    setIsLoading(false)
                }
            }
            Log.d("VideoViewModel", "Finished receiving video list")
        }
    }


    @RequiresApi(Build.VERSION_CODES.O)
    fun renameVideo(oldName: String, newName: String) {
        viewModelScope.launch(Dispatchers.IO) {
            var socket: Socket? = null
            var auth: String = "video_rename"
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair<String, String>("192.168.1.17", "42069")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }
            val socketAddress = addressPair?.second?.let {
                InetSocketAddress(
                    addressPair.first,
                    it.toInt()
                )
            }

            try {
                socket = Socket()
                socket.connect(socketAddress, 2000)
                val videoOutputStream = DataOutputStream(socket.getOutputStream())
                val videoInputStream = DataInputStream(socket.getInputStream())

                videoOutputStream.write(auth.toByteArray(Charsets.UTF_8))
                videoOutputStream.flush()

                val videoResponse = BufferedReader(InputStreamReader(videoInputStream)).readLine()

                videoOutputStream.write(oldName.toByteArray(Charsets.UTF_8))
                videoOutputStream.flush()

                videoOutputStream.write(newName.toByteArray(Charsets.UTF_8))
                videoOutputStream.flush()
            } catch (e: Exception) {
                Log.d("VideoViewModel", "Error renaming video: ${e.message}")
            } finally {
                socket?.close()
            }
        }
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun deleteVideo(videoName: String)
    {
        viewModelScope.launch(Dispatchers.IO) {
            var socket: Socket? = null
            var auth: String = "video_delete"
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair<String, String>("192.168.1.17", "42069")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, DOWNLOAD_FILE_PATH, BRANCH_NAME)
            }
            val socketAddress = addressPair?.second?.let {
                InetSocketAddress(
                    addressPair.first,
                    it.toInt()
                )
            }

            try {
                socket = Socket()
                socket.connect(socketAddress, 2000)
                val videoOutputStream = DataOutputStream(socket.getOutputStream())
                val videoInputStream = DataInputStream(socket.getInputStream())

                videoOutputStream.write(auth.toByteArray(Charsets.UTF_8))
                videoOutputStream.flush()

                val videoResponse = BufferedReader(InputStreamReader(videoInputStream)).readLine()

                videoOutputStream.write(videoName.toByteArray(Charsets.UTF_8))
                videoOutputStream.flush()
            }
            catch (e: Exception) {
                Log.d("VideoViewModel", "Error deleting video: ${e.message}")
            } finally {
                socket?.close()
            }
        }
    }

    fun setIsLoading(newValue: Boolean)
    {
        savedStateHandle[VIDEO_STATE_KEY] = _videoState2.value.copy(
            isLoading = newValue,
        )
        _videoState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                isLoading = newValue,
            )
        }
    }

    fun setVideos(newVideos: MutableList<Video>)
    {
        savedStateHandle[VIDEO_STATE_KEY] = _videoState2.value.copy(
            videos = newVideos,
        )
        _videoState1.update { currVideoState ->
            currVideoState.copy(
                videos = newVideos,
            )
        }
    }

    fun setRefresh(newValue: Boolean)
    {
        savedStateHandle[VIDEO_STATE_KEY] = _videoState2.value.copy(
            refresh = newValue,
        )
        _videoState1.update { currVideoState ->
            currVideoState.copy(
                refresh = newValue,
            )
        }
    }
}

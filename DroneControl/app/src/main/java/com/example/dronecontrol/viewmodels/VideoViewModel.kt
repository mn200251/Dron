package com.example.dronecontrol.viewmodels

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Parcelable
import android.util.Base64
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.DataInputStream
import java.io.DataOutputStream
import java.net.Socket
import org.json.JSONObject
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.State
import androidx.lifecycle.SavedStateHandle
import com.example.dronecontrol.data_types.InstructionType
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

    fun fetchVideos() {
        viewModelScope.launch(Dispatchers.IO) {
            var socket = Socket()
            val socketAddress = InetSocketAddress("192.168.1.17", 6969)


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
}

package com.example.phonedelaytest.viewmodels

import android.os.Build
import android.os.Parcelable
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.phonedelaytest.retrofit.RetrofitClient
import com.example.phonedelaytest.viewmodels.ControlsEnum.*
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.parcelize.Parcelize
import java.io.BufferedReader
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.InputStream
import java.io.InputStreamReader
import java.io.ObjectOutputStream
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.coroutines.resume
import kotlin.io.encoding.ExperimentalEncodingApi

@Parcelize
data class ControlsState(
    var up: Int = 0,
    var down: Int = 0,
    var left: Int = 0,
    var right: Int = 0,
) : Parcelable

enum class ControlsEnum {
    UP,
    DOWN,
    LEFT,
    RIGHT
}

const val UI_STATE_KEY = "uiState"

class ConnectionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _uiState1 = MutableStateFlow(ControlsState())

    private val _uiState2 = savedStateHandle.getStateFlow(UI_STATE_KEY, ControlsState())

    val uiState = _uiState2

    private val host: String = "178.148.73.92"
    private val port: Int = 6969
    // private val sendControls: AtomicBoolean = AtomicBoolean(false)
    private val mutex = Mutex(false)
    private var sendControls = false

    private val apiService = RetrofitClient.create()


    fun updateControls(pressedControl: ControlsEnum) {

        viewModelScope.launch(Dispatchers.Default) {
            // mutex.lock()

            when (pressedControl) {
                UP -> {
                    savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
                        up = uiState.value.up++,
                    )
                    _uiState1.update { currentCaloriesUiState ->
                        currentCaloriesUiState.copy(
                            up = uiState.value.up++,
                        )
                    }
                }

                DOWN -> {
                    savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
                        down = uiState.value.down++,
                    )
                    _uiState1.update { currentCaloriesUiState ->
                        currentCaloriesUiState.copy(
                            down = uiState.value.down++,
                        )
                    }
                }

                LEFT -> {
                    savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
                        left = uiState.value.left++,
                    )
                    _uiState1.update { currentCaloriesUiState ->
                        currentCaloriesUiState.copy(
                            left = uiState.value.left++,
                        )
                    }
                }

                RIGHT -> {
                    savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
                        right = uiState.value.right++,
                    )
                    _uiState1.update { currentCaloriesUiState ->
                        currentCaloriesUiState.copy(
                            right = uiState.value.right++,
                        )
                    }
                }

            }

            sendControls = true
            // mutex.unlock()
        }
    }


    fun resetControls()
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            right = 0,
            left = 0,
            up = 0,
            down = 0,
        )
        _uiState1.update { currentCaloriesUiState ->
            currentCaloriesUiState.copy(
                right = 0,
                left = 0,
                up = 0,
                down = 0,
            )
        }
    }


    fun sendControl(control: String, num: Int, outputStream: OutputStream)
    {
        var i = 0
        while (i < num)
        {
            Log.d("Sent", "Sent controlls!")
            outputStream.write(control.toByteArray(Charsets.UTF_8))
            outputStream.flush()
            i++
        }
    }

    fun startController() {
        viewModelScope.launch(Dispatchers.Default) {

            var socket = Socket()
            val socketAddress = InetSocketAddress(host, port)

            try {
                socket.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket.getOutputStream()
                val inputStream: InputStream = socket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))

                try {
                    outputStream.write("User - Controls\n".toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    while (true) {
                        while (true) {
                            // mutex.lock()

                            if (sendControls)
                            {
                                sendControls = false
                                break
                            }

                            // mutex.unlock()
                            delay(3)
                        }

                        sendControl("U", uiState.value.up, outputStream)
                        sendControl("D", uiState.value.down, outputStream)
                        sendControl("L", uiState.value.left, outputStream)
                        sendControl("R", uiState.value.right, outputStream)

                        resetControls()

                        // mutex.unlock()





                        /*
                        val toSend = uiState.value.copy()

                        resetControls()

                        mutex.unlock()

                        Log.d("Sent", "Sent controlls!")
                        outputStream.write(toSend.toString().toByteArray(Charsets.UTF_8))
                        outputStream.flush()
                        */

                    }
                } catch (e: Exception) {
                    Log.d("Connection2 Exception", e.message.toString())
                } finally {
                    outputStream.close()
                    reader.close()
                    inputStream.close()
                    socket.close()
                }

            } catch (ex: Exception) {
                Log.d("Connection Exception", ex.message.toString())
                socket.close()
            }
        }
    }


    fun pingServer() {
        viewModelScope.launch(Dispatchers.Default) {
            try {
                // var response = apiService?.fetchData()

                apiService?.sendData("First message".toByteArray(Charsets.UTF_8))

                var response = apiService?.fetchData()

                Log.d("Response", "Received response from server:$response")

                apiService?.sendData("Second message".toByteArray(Charsets.UTF_8)
                )

            } catch (e: Exception) {
                Log.d("Connection Exception", e.message.toString())
            }
        }
    }

    @OptIn(ExperimentalEncodingApi::class)
    fun getDelay()
    {
        viewModelScope.launch(Dispatchers.Default) {

            var socket = Socket()
            val socketAddress = InetSocketAddress(host, port)

            try {
                socket.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket.getOutputStream()
                val inputStream: InputStream = socket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))
                val reader2 = BufferedReader(InputStreamReader(inputStream, Charsets.UTF_8))
                val dataInputStream = DataInputStream(inputStream)

                try {
                    outputStream.write("First message".toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    var i = 0
                    val maxIterations = 1000

                    while (i < maxIterations)
                    {
                        // var response = dataInputStream.readUTF()
                        var text = BufferedReader(InputStreamReader(socket.inputStream)).readLine()
                        // val response2 = reader.readLine().toString()

                        Log.d("Response", "Received response from server:$text")

                        outputStream.write("Second message".toByteArray(Charsets.UTF_8))
                        outputStream.flush()

                        i++
                    }

                } catch (e: Exception) {
                    Log.d("Connection2 Exception", e.message.toString())
                }
                finally {
                    outputStream.close()
                    reader.close()
                    // dataInputStream.close()
                    inputStream.close()
                    socket.close()
                }
            }
            catch (ex: Exception)
            {
                Log.d("Connection Exception", ex.message.toString())
                socket.close()
            }

        }

    }
}

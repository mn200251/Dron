package com.example.dronecontrol.viewmodels

import android.os.Parcelable
import android.util.Log
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.parcelize.Parcelize
import kotlinx.parcelize.RawValue
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket


@Parcelize
data class ConnectionState(
    var host: String = "",
    var port: String = "",
    var mainScreenErrorText: String = "",
    var screenNumber: SCREEN = SCREEN.DroneScreen,
    // @RawValue var socket: Socket? = null
) : Parcelable

const val UI_STATE_KEY = "uiState"

enum class SCREEN{
    MainScreen,
    DroneScreen
}

class ConnectionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _uiState1 = MutableStateFlow(ConnectionState())

    private val _uiState2 = savedStateHandle.getStateFlow(UI_STATE_KEY, ConnectionState())

    val uiState = _uiState2


    private fun updateScreen(newScreen: SCREEN)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            screenNumber = newScreen,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                screenNumber = newScreen,
            )
        }
    }


    fun updateHost(newHost: String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            host = newHost,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                host = newHost,
            )
        }
    }

    fun updatePort(newPort: String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            port = newPort,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                port = newPort,
            )
        }
    }

    fun updateMainScreenErrorText(newError:String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            mainScreenErrorText = newError,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                mainScreenErrorText = newError,
            )
        }
    }

    fun connect2Server()
    {
        viewModelScope.launch(Dispatchers.Default)
        {
            // check if host is correct ipv4 address
            val ipv4Regex = """^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$""".toRegex()
            val isIPv4 = ipv4Regex.matches(uiState.value.host)

            if (!isIPv4)
            {
                updateMainScreenErrorText("IP Address is incorrect format!")
                return@launch
            }

            // try to convert port to int
            try {
                val port: Int = uiState.value.port.toInt()
            }
            catch (e: NumberFormatException)
            {
                updateMainScreenErrorText("Port must be an Integer!")
                return@launch
            }

            var socket = Socket()
            val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())

            try{
                socket.connect(socketAddress, 2000)

                val outputStream: OutputStream = socket.getOutputStream()
                val inputStream: InputStream = socket.getInputStream()
                val reader = BufferedReader(InputStreamReader(inputStream))

                try {
                    // authenticate user
                    val auth: String = "TestUser"
                    outputStream.write(auth.toByteArray(Charsets.UTF_8))
                    outputStream.flush()

                    var response = BufferedReader(InputStreamReader(socket.inputStream)).readLine()
                    Log.d("Response", "Received response from server:$response")

                    if (response == "1") // drone not connected, wait?
                    {

                    }
                    else if (response != "0") // an unknown error has occured
                    {
                        updateMainScreenErrorText("An unknown internal server error has occured!")
                        return@launch
                    }

                    // save socket connection somehow
                    // start 1 thread for controls
                    updateMainScreenErrorText("")

                    updateScreen(SCREEN.DroneScreen)
                    receiveVideoStream(socket)

                } catch (e: Exception) {

                } finally {
                    outputStream.close()
                    reader.close()
                    inputStream.close()
                }
            } catch (e: Exception) {
                Log.d("Connection Exception", e.message.toString())
                updateMainScreenErrorText("An error has occurred while connecting to the server!")
                return@launch
            } finally {
                // socket.close()
            }
        }
    }

    // called from thread that connects to server
    private fun receiveVideoStream(socket: Socket)
    {
        val inputStream: InputStream = socket.getInputStream()
        // val reader = BufferedReader(InputStreamReader(inputStream))

        try {
            while (true)
            {
                var response = BufferedReader(InputStreamReader(socket.inputStream)).readLine()

                // update frame shown on phone
            }
        }
        catch (e: Exception)
        {
            Log.d("Error receiving video", e.message.toString())
        }
        finally {
            inputStream.close()
        }
    }


}
package com.example.dronecontrol.viewmodels

import android.os.Parcelable
import android.util.Log
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.parcelize.Parcelize
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket

import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json


@Parcelize
data class ConnectionState(
    var host: String = "",
    var port: String = "",
    var mainScreenErrorText: String = "",
    var screenNumber: SCREEN = SCREEN.MainScreen,

    var joystickX: Float = 0f,
    var joystickY: Float = 0f,
    var SliderZ: Float = 0f,
    var isSendingMovement: Boolean = false,
    var connectionActive: Boolean = false,

    // @RawValue var socket: Socket? = null
) : Parcelable

const val UI_STATE_KEY = "uiState"

enum class SCREEN{
    MainScreen,
    DroneScreen
}

@Serializable
data class Coordinates(val x: Float, val y: Float, val z: Float)


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

    // x and y are normalized to 0-1
    fun updateJoystickMovement(x: Float, y: Float)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickX = x,
            joystickY = y,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickX = x,
                joystickY = y,
            )
        }
    }

    fun updateIsSendingMovement(isSendingMovement: Boolean)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            isSendingMovement = isSendingMovement
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                isSendingMovement = isSendingMovement
            )
        }
    }

    fun updateConnectionActive(connectionActive: Boolean)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            connectionActive = connectionActive
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                connectionActive = connectionActive
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
                        updateMainScreenErrorText("An unknown internal server error has occured!")
                        return@launch
                    }
                    // response == 0 - drone connected

                    // start 1 thread for controls
                    updateMainScreenErrorText("")

                    updateScreen(SCREEN.DroneScreen)
                    updateConnectionActive(true)

                    socket.tcpNoDelay = true

                    viewModelScope.launch(Dispatchers.Default)
                    {
                        sendMovement(socket)
                    }

                    // called from thread that connects to server
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
                // connectionActive will be false
                updateScreen(SCREEN.DroneScreen)

                socket.close()
            }
        }
    }

    // called from thread that connects to server
    private fun receiveVideoStream(socket: Socket)
    {
        val inputStream: InputStream = socket.getInputStream()
        // val reader = BufferedReader(InputStreamReader(inputStream))

        try {
            while (uiState.value.connectionActive)
            {
                // var response = BufferedReader(InputStreamReader(socket.inputStream)).readLine()

                // update frame shown on phone
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
    }

    private fun createAndSendJson(outputStream: OutputStream, x: Float, y: Float, z: Float) {
        // Step 2: Serialize the data class instance to a JSON string
        val coordinates = Coordinates(x, y, z)
        val jsonString = Json.encodeToString(coordinates)

        outputStream.write(jsonString.toByteArray(Charsets.UTF_8))
        outputStream.flush()
    }

    suspend fun sendMovement(socket: Socket)
    {
        val outputStream: OutputStream = socket.getOutputStream()
        // val coordinates = Coordinates(0f, 0f, 0f)

        try {
            while(uiState.value.connectionActive)
            {
                if (uiState.value.isSendingMovement)
                {
                    // turning left right
                    createAndSendJson(outputStream, uiState.value.joystickX, uiState.value.joystickY, uiState.value.SliderZ)

                    delay(10)
                }
                else
                {
                    delay(100)
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
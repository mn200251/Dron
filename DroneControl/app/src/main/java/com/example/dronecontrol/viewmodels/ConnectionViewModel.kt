package com.example.dronecontrol.viewmodels

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.os.Parcelable
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.FILE_PATH
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.REPO_NAME
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.parcelize.Parcelize
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.kohsuke.github.GHRepository
import org.kohsuke.github.GitHubBuilder
import java.io.BufferedReader
import java.io.DataInputStream
import java.io.InputStream
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.util.Base64
import kotlin.io.encoding.ExperimentalEncodingApi


@Parcelize
data class ConnectionState(
    // var host: String = "",
    // var port: String = "",
    var mainScreenErrorText: String = "",
    var screenNumber: SCREEN = SCREEN.MainScreen,

    var joystickX: Float = 0f,
    var joystickY: Float = 0f,
    var joystickZ: Float = 0f,
    var joystickRotation: Float = 0f,

    var isSendingMovement: Boolean = false,
    var connectionActive: Boolean = false,

    var frame: Bitmap? = null,

    // @RawValue var socket: Socket? = null
) : Parcelable

const val UI_STATE_KEY = "uiState"

enum class SCREEN{
    MainScreen,
    DroneScreen,
    VideoListScreen
}

@Serializable
data class Coordinates(val x: Float, val y: Float, val z: Float, val rotation: Float)


class ConnectionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _uiState1 = MutableStateFlow(ConnectionState())

    private val _uiState2 = savedStateHandle.getStateFlow(UI_STATE_KEY, ConnectionState())

    val uiState = _uiState2

    val internal=true

    @RequiresApi(Build.VERSION_CODES.O)
    @OptIn(ExperimentalEncodingApi::class)
    suspend fun getCurrentIP(githubToken: String, repoName: String, filePath: String, branchName: String): Pair<String, String>? {
        return withContext(Dispatchers.IO) {
            try {
                // Authenticate to GitHub
                val github = GitHubBuilder().withOAuthToken(githubToken).build()

                // Get the repository
                val repo: GHRepository = github.getRepository(repoName)

                // Get the file contents
                val file = repo.getFileContent(filePath, branchName)
                val inputStream: InputStream = file.read()
                val decodedContent = inputStream.readBytes().toString(Charsets.UTF_8).trim()

                Log.d("decodedContent", decodedContent)

                // Split the IP address and port
                val parts = decodedContent.split(":")

                if (parts.size == 2) {
                    val ip = parts[0].trim()

                    var port = parts[1].trim()
                    try {
                        val portTest = parts[1].trim().toInt()
                    }
                    catch(e: NumberFormatException) {
                        println("Port is not type int!")
                        return@withContext null
                    }

                    return@withContext Pair(ip, port)
                } else {
                    println("The content format is incorrect.")
                    return@withContext null
                }
            } catch (e: Exception) {
                println("An error occurred: ${e.message}")
                return@withContext null
            }
        }
    }

    fun updateScreen(newScreen: SCREEN)
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

    /*

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
     */

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
    fun updateRightJoystickMovement(x: Float, y: Float)
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

    fun updateLeftJoystickMovement(normalizedX: Float, normalizedY: Float) {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickZ = normalizedX,
            joystickRotation = normalizedY,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickZ = normalizedX,
                joystickRotation = normalizedY,
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

    fun updateConnectionActive(connectionActive: Boolean) {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            connectionActive = connectionActive
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                connectionActive = connectionActive
            )
        }
    }

    private fun resetControls()
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickX = 0f,
            joystickY = 0f,
            joystickZ = 0f,
            joystickRotation = 0f,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickX = 0f,
                joystickY = 0f,
                joystickZ = 0f,
                joystickRotation = 0f,
            )
        }
    }

    fun updateFrame(newFrame: Bitmap)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            frame = newFrame
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                frame = newFrame
            )
        }
    }

    @RequiresApi(Build.VERSION_CODES.O)
    fun connect2Server()
    {
        viewModelScope.launch(Dispatchers.Default)
        {

            val addressPair= getCurrentIP(GITHUB_TOKEN, REPO_NAME, FILE_PATH, BRANCH_NAME)

            if (addressPair == null)
            {
                updateMainScreenErrorText("Unable to obtain server IP!")
                return@launch
            }

            Log.d("IP", addressPair.first + ":" + addressPair.second)



            var socket = Socket()
            var socketAddress: InetSocketAddress? =null
            // val socketAddress = InetSocketAddress(uiState.value.host, uiState.value.port.toInt())
            if (internal){
                 socketAddress = InetSocketAddress("192.168.1.17", 6969)
            }else {
                 socketAddress = InetSocketAddress(addressPair.first, addressPair.second.toInt())
            }
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
                updateScreen(SCREEN.MainScreen)

                socket.close()
            }
        }
    }

    // called from thread that connects to server
    private fun receiveVideoStream(socket: Socket)
    {
        val inputStream: InputStream = socket.getInputStream()
        val dataInputStream: DataInputStream = DataInputStream(inputStream)

        try {
            while (uiState.value.connectionActive)
            {
                val size: Int = dataInputStream.readInt()

                // Read the JPEG data
                val jpegData = ByteArray(size)
                dataInputStream.readFully(jpegData)

                // Convert JPEG data to Bitmap
                val bitmap = BitmapFactory.decodeByteArray(jpegData, 0, size)

                updateFrame(bitmap)

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

    private fun createAndSendJson(outputStream: OutputStream, x: Float, y: Float, z: Float, rotation: Float) {
        // Step 2: Serialize the data class instance to a JSON string
        val coordinates = Coordinates(x, y, z, rotation)
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
                // if (uiState.value.isSendingMovement)
                if (uiState.value.joystickX != 0f || uiState.value.joystickY != 0f ||
                    uiState.value.joystickZ != 0f || uiState.value.joystickRotation != 0f)
                {
                    // turning left right
                    createAndSendJson(outputStream, uiState.value.joystickX, uiState.value.joystickY, uiState.value.joystickZ, uiState.value.joystickRotation)

                    delay(100)
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
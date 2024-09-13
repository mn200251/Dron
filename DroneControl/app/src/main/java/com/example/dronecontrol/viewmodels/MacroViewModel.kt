package com.example.dronecontrol.viewmodels

import android.graphics.BitmapFactory
import android.os.Build
import android.os.Parcelable
import android.util.Base64
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.dronecontrol.data_types.InstructionType
import com.example.dronecontrol.private.BRANCH_NAME
import com.example.dronecontrol.private.DOWNLOAD_FILE_PATH
import com.example.dronecontrol.private.GITHUB_TOKEN
import com.example.dronecontrol.private.INTERNAL
import com.example.dronecontrol.private.REPO_NAME
import com.example.dronecontrol.private.SERVER_FILE_PATH
import com.example.dronecontrol.utils.getCurrentIP
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.parcelize.Parcelize
import org.json.JSONObject
import java.io.BufferedReader
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.InputStreamReader
import java.net.InetSocketAddress
import java.net.Socket


@Parcelize
data class MacroState(
    val macroList: List<String> = emptyList(),
    var isLoading: Boolean = false
) : Parcelable

const val MACRO_STATE_KEY = "macroState"

class MacroViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _macroState1 = MutableStateFlow(MacroState())

    private val _macroState2 = savedStateHandle.getStateFlow(MACRO_STATE_KEY, MacroState())

    val uiState = _macroState2


    @RequiresApi(Build.VERSION_CODES.O)
    fun fetchMacros() {
        viewModelScope.launch(Dispatchers.IO) {
            setIsLoading(true)

            var socket: Socket? = null
            var auth: String = "macro"
            var addressPair: Pair<String, String>?
            if (INTERNAL) {
                addressPair = Pair("192.168.1.17", "6969")
            } else {
                addressPair = getCurrentIP(GITHUB_TOKEN, REPO_NAME, SERVER_FILE_PATH, BRANCH_NAME)
            }
            val socketAddress = addressPair?.second?.let {
                InetSocketAddress(
                    addressPair.first,
                    it.toInt()
                )
            }
            var numberOfMacros = 0

            val macroList = mutableListOf<String>()
            var cnt = -1
            while (cnt < numberOfMacros) {
                try {
                    socket = Socket()
                    socket.connect(socketAddress, 2000)
                    val videoOutputStream = DataOutputStream(socket.getOutputStream())
                    val reader = BufferedReader(InputStreamReader(socket.getInputStream()))

                    videoOutputStream.write(auth.toByteArray(Charsets.UTF_8))
                    videoOutputStream.flush()

                    if (cnt == -1) {

                        val request = JSONObject().apply {
                            put("type", InstructionType.GET_MACROS.value)
                        }

                        videoOutputStream.writeUTF(request.toString())
                        videoOutputStream.flush()

                        numberOfMacros = reader.readLine().toInt()
                        Log.d("MacroViewModel", "Number of macros: $numberOfMacros")
                        cnt = 0
                    }

                    while (cnt < numberOfMacros) {
                        val newMacro = reader.readLine()

                        macroList.add(newMacro)

                        val updatedMacros = macroList.toMutableList()

                        setMacroList(updatedMacros)
                        cnt++
                    }
                } catch (e: Exception) {
                    // Handle exceptions and retry logic if necessary
                    Log.d("MacroViewModel", "Error receiving macro ${cnt}: ${e.message}")
                } finally {
                    socket?.close()

                    setIsLoading(false)
                }
            }
            Log.d("MacroViewModel", "Finished receiving macro list")
        }
    }

    private fun setIsLoading(newValue: Boolean) {
        savedStateHandle[MACRO_STATE_KEY] = _macroState2.value.copy(
            isLoading = newValue,
        )
        _macroState1.update { currMacroState ->
            currMacroState.copy(
                isLoading = newValue,
            )
        }
    }

    private fun setMacroList(newMacros: MutableList<String>) {
        savedStateHandle[MACRO_STATE_KEY] = _macroState2.value.copy(
            macroList = newMacros,
        )
        _macroState1.update { currMacroState ->
            currMacroState.copy(
                macroList = newMacros,
            )
        }
    }
}
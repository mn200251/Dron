package com.example.dronecontrol.sharedRepositories

import android.graphics.Bitmap
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.example.dronecontrol.viewmodels.SCREEN

object SharedRepository {

    // Internal MutableLiveData to store and observe the frame
    private val _frame = MutableLiveData<Bitmap?>()
    val frame: LiveData<Bitmap?> get() = _frame

    // Internal MutableLiveData to store and observe the main screen error text
    private val _mainScreenErrorText = MutableLiveData<String>()
    val mainScreenErrorText: LiveData<String> get() = _mainScreenErrorText

    // Internal MutableLiveData to store and observe the screen number
    private val _screenNumber = MutableLiveData<SCREEN>(SCREEN.MainScreen)
    val screenNumber: LiveData<SCREEN> get() = _screenNumber

    // Thread-safe setter for frame
    fun setFrame(newFrame: Bitmap?) {
        _frame.postValue(newFrame)
    }

    // Thread-safe setter for mainScreenErrorText
    fun setMainScreenErrorText(errorText: String) {
        _mainScreenErrorText.postValue(errorText)
    }

    // Thread-safe setter for screenNumber
    fun setScreen(newScreenNumber: SCREEN) {
        _screenNumber.postValue(newScreenNumber)
    }

    // Thread-safe getters (in case you need them outside LiveData observation)
    fun getFrame(): Bitmap? = _frame.value

    fun getMainScreenErrorText(): String = _mainScreenErrorText.value ?: ""

    fun getScreen(): SCREEN = _screenNumber.value ?: SCREEN.MainScreen
}
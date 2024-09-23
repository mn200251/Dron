package com.example.dronecontrol.sharedRepositories

import android.graphics.Bitmap
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.example.dronecontrol.viewmodels.SCREEN

object SharedRepository {
    private val _frame = MutableLiveData<Bitmap?>()
    val frame: LiveData<Bitmap?> get() = _frame

    private val _mainScreenErrorText = MutableLiveData<String>()
    val mainScreenErrorText: LiveData<String> get() = _mainScreenErrorText

    private val _screenNumber = MutableLiveData<SCREEN>(SCREEN.MainScreen)
    val screenNumber: LiveData<SCREEN> get() = _screenNumber

    private val _isPoweredOn = MutableLiveData<Boolean>(false)
    val isPoweredOn: LiveData<Boolean> get() = _isPoweredOn

    private val _isPidOn = MutableLiveData<Boolean>(false)
    val isPidOn: LiveData<Boolean> get() = _isPidOn

    private val _isRecordingMacro = MutableLiveData<Boolean>(false)
    val isRecordingMacro: LiveData<Boolean> get() = _isRecordingMacro

    private val _isRecordingVideo = MutableLiveData<Boolean>(false)
    val isRecordingVideo: LiveData<Boolean> get() = _isRecordingVideo

    // Thread-safe setter for frame
    fun setFrame(newFrame: Bitmap?) {
        // var oldFrame = _frame.value

        _frame.postValue(newFrame)

        // oldFrame?.recycle()
    }

    // Thread-safe setter for mainScreenErrorText
    fun setMainScreenErrorText(errorText: String) {
        _mainScreenErrorText.postValue(errorText)
    }

    // Thread-safe setter for screenNumber
    fun setScreen(newScreenNumber: SCREEN) {
        _screenNumber.postValue(newScreenNumber)
    }

    fun setPoweredOn(newValue: Boolean)
    {
        _isPoweredOn.postValue(newValue)
    }

    fun setPidOn(newValue: Boolean)
    {
        _isPidOn.postValue(newValue)
    }

    fun setRecordingMacro(newValue: Boolean)
    {
        _isRecordingMacro.postValue(newValue)
    }

    fun setRecordingVideo(newValue: Boolean)
    {
        _isRecordingVideo.postValue(newValue)
    }

    // Thread-safe getters (in case you need them outside LiveData observation)
    fun getFrame(): Bitmap? = _frame.value

    fun getMainScreenErrorText(): String = _mainScreenErrorText.value ?: ""

    fun getScreen(): SCREEN = _screenNumber.value ?: SCREEN.MainScreen

    fun getPoweredOn(): Boolean = _isPoweredOn.value ?: false

    fun getPidOn(): Boolean = _isPidOn.value ?: false

    fun getRecordingMacro(): Boolean = _isRecordingMacro.value ?: false

    fun getRecordingVideo(): Boolean = _isRecordingVideo.value ?: false
}
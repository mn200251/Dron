package com.example.dronecontrol.screens

import android.graphics.Bitmap
import android.graphics.Color.rgb
import android.graphics.Paint
import android.os.Build
import android.util.Log
import android.view.MotionEvent
import androidx.annotation.RequiresApi
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.models.ModifiedJoyStick
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import kotlin.math.roundToInt
import kotlin.math.sqrt


@RequiresApi(Build.VERSION_CODES.R)
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun DroneScreen(connectionViewModel: ConnectionViewModel = viewModel())
{
    // button for taking pictures?
    // battery percentage
    // forward back left right
    // up down
    // stop button

    val uiState by connectionViewModel.uiState.collectAsState()

    var frame by remember { mutableStateOf<ImageBitmap?>(null) }

    val width = LocalConfiguration.current.screenWidthDp.dp
    val height = LocalConfiguration.current.screenHeightDp.dp

    var rightJoystickVisible by remember { mutableStateOf(false) }
    var leftJoystickVisible by remember { mutableStateOf(false) }
    var joystickPosition by remember { mutableStateOf(Offset(0f, 0f)) }
    var dotPosition by remember { mutableStateOf(Offset(0f, 0f)) }

    val currLocalDensity = LocalDensity.current

    val joystickSize = 160
    val invisibleAreaStartX = 1300f  // Start x coordinate of invisible area
    val invisibleAreaStartY = 400f // Start y coordinate of invisible area
    val invisibleAreaEndX = 2600f   // End x coordinate of invisible area
    val invisibleAreaEndY = 1920f   // End y coordinate of invisible area

    // var sendMovementJob: Job? by remember { mutableStateOf(null) }

    /*
    LaunchedEffect(Unit) {
        var i = 255
        while (true) {
            if (i == 0)
                i = 255


            // Receive video frame here (e.g., from network or file)
            // Update the 'frame' variable with the received frame
            frame = createDummyBitmap(width, height, i) // Replace this with actual video frame
            delay(15L) // 60fps
            i--
        }
    }



    Canvas(modifier = Modifier.fillMaxSize()) {
        frame?.let {
            drawImage(it, topLeft = Offset.Zero)
        }
    }
    */
    Canvas(modifier = Modifier.fillMaxSize()) {
        // uiState.frame?.let {
        //     drawImage(it.asImageBitmap(), topLeft = Offset.Zero)
        // }
        uiState.frame?.let { bitmap ->
            val canvasWidth = size.width
            val canvasHeight = size.height

            val imageWidth = bitmap.width
            val imageHeight = bitmap.height

            val scaleX = canvasWidth / imageWidth
            val scaleY = canvasHeight / imageHeight
            val scale = kotlin.math.max(scaleX, scaleY)

            withTransform({
                scale(scale, scale, pivot = Offset.Zero)
            }) {
                drawImage(bitmap.asImageBitmap(), topLeft = Offset.Zero)
            }
        }
    }


    Box(modifier = Modifier
        .fillMaxSize()
        .pointerInteropFilter { event ->
            // val adjustmentOffset = 45f
            val adjustmentOffset = joystickSize / 4f

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    if (event.x in invisibleAreaStartX..invisibleAreaEndX && event.y in invisibleAreaStartY..invisibleAreaEndY) {

                        rightJoystickVisible = true
                        joystickPosition = Offset(event.x, event.y)
                        dotPosition = Offset(adjustmentOffset, adjustmentOffset)

                        Log.d(
                            "Joystick",
                            "${dotPosition.x - adjustmentOffset}, ${dotPosition.y - adjustmentOffset}"
                        )

                        connectionViewModel.updateIsSendingMovement(true)

                    }
                    true
                }

                MotionEvent.ACTION_MOVE -> {
                    if (rightJoystickVisible) {
                        var maxOffset: Float
                        with(currLocalDensity)
                        {
                            maxOffset = (joystickSize / 4).dp.toPx()
                        }

                        val x = event.x - joystickPosition.x
                        val y = event.y - joystickPosition.y
                        val distance = sqrt(x * x + y * y)
                        val constrainedX =
                            if (distance > maxOffset) x * (maxOffset / distance) else x
                        val constrainedY =
                            if (distance > maxOffset) y * (maxOffset / distance) else y
                        dotPosition =
                            Offset(constrainedX + adjustmentOffset, constrainedY + adjustmentOffset)

                        val normalizedX = (dotPosition.x - adjustmentOffset) / maxOffset
                        val normalizedY = (dotPosition.y - adjustmentOffset) / maxOffset

                        Log.d(
                            "Joystick",
                            "${normalizedX}, ${normalizedY}"
                        )

                        connectionViewModel.updateJoystickMovement(normalizedX, normalizedY)

                        //dotPosition = Offset(x, y)
                    }
                    true
                }

                MotionEvent.ACTION_UP -> {
                    rightJoystickVisible = false

                    connectionViewModel.updateJoystickMovement(0f, 0f)
                    connectionViewModel.updateIsSendingMovement(false)
                    // sendMovementJob?.cancel()
                    // sendMovementJob = null
                    true
                }

                else -> false
            }
        }
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Your column content here
        }

        /*
        JoyStick(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(30.dp),
            size = 200.dp,
            dotSize = 30.dp,
        ) { x: Float, y: Float ->
            Log.d("JoyStick", "$x, $y")
        }
        */

        if (rightJoystickVisible) {
            ModifiedJoyStick(
                modifier = Modifier
                    //.align(Alignment.BottomEnd)
                    .offset {
                        IntOffset(
                            joystickPosition.x.roundToInt() - 250,
                            joystickPosition.y.roundToInt() - 250
                        )
                    } // Adjust the offset to center the joystick
                    .size(joystickSize.dp)
                    .padding(30.dp),
                size = joystickSize.dp,
                dotSize = (joystickSize / 6).dp,
                dotOffset = dotPosition
            ) { x: Float, y: Float ->
                Log.d("JoyStick", "$x, $y")
            }
        }
    }

}


// Function to create a dummy bitmap (replace with actual video frame creation logic)
fun createDummyBitmap(width: Dp, height: Dp, i: Int): ImageBitmap {
    // val width = LocalConfiguration.current.screenWidthDp.dp
    // val height = LocalConfiguration.current.screenHeightDp.dp
    val width2 = 3150
    val height2 = 1450
    // val bitmap = Bitmap.createBitmap(width.value.toInt(), height.value.toInt(), Bitmap.Config.ARGB_8888)
    val bitmap = Bitmap.createBitmap(width2, height2, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    // Draw dummy content on the canvas
    canvas.drawColor(rgb(i - 70, i - 140, i))
    // canvas.drawColor(Color.White) // Background color
    canvas.drawRect(0f + 10 * i, 0f, 200f + 10f * i, 150f, Paint().apply { color = rgb(255 - i * 4, i, 0) }) // Example rectangle
    // canvas.drawText("Hello, World!", 100f, 200f, Paint().apply { color = rgb(0, 0, 0) }) // Example text

    return bitmap.asImageBitmap()
}

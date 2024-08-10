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
import androidx.compose.material3.Text
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
import androidx.compose.ui.input.pointer.PointerInputScope
import androidx.compose.ui.input.pointer.changedToDown
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.input.pointer.positionChangeConsumed
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.times
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.collectAsState
import com.example.dronecontrol.models.ModifiedJoyStick
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import kotlin.math.roundToInt
import kotlin.math.sqrt


@Composable
fun DroneScreen(connectionViewModel: ConnectionViewModel = viewModel())
{
    // button for taking pictures?
    // battery percentage
    // forward back left right
    // up down
    // stop button

    val uiState by connectionViewModel.uiState.collectAsState()

    val width = LocalConfiguration.current.screenWidthDp.dp
    val height = LocalConfiguration.current.screenHeightDp.dp

    var rightJoystickVisible by remember { mutableStateOf(false) }
    var leftJoystickVisible by remember { mutableStateOf(false) }

    var leftJoystickPosition by remember { mutableStateOf(Offset(0f, 0f)) }
    var rightJoystickPosition by remember { mutableStateOf(Offset(0f, 0f)) }

    var rightDotPosition by remember { mutableStateOf(Offset(0f, 0f)) }
    var leftDotPosition by remember { mutableStateOf(Offset(0f, 0f)) }

    val frame by SharedRepository.frame.collectAsState(null) // Use a default value

    val currLocalDensity = LocalDensity.current

    val joystickAreaWidth = 0.45f
    val joystickAreaHeight = 0.65f

    val joystickSize = 160

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

        // SharedRepository.getFrame()?.let { bitmap ->
        frame?.let { bitmap: Bitmap ->
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

    /*
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        with(LocalDensity.current) {
            val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
            val screenHeightDp = LocalConfiguration.current.screenHeightDp.dp

            Box(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .size(width = 0.45f * screenWidthDp, height = 0.65f * screenHeightDp)
                    .pointerInteropFilter { event ->
                        val adjustmentOffset = joystickSize / 4f

                        when (event.action) {
                            MotionEvent.ACTION_DOWN -> {
                                rightJoystickVisible = true
                                joystickPosition = Offset(event.x, event.y)
                                dotPosition = Offset(adjustmentOffset, adjustmentOffset)

                                Log.d(
                                    "Joystick",
                                    "${dotPosition.x - adjustmentOffset}, ${dotPosition.y - adjustmentOffset}"
                                )

                                connectionViewModel.updateIsSendingMovement(true)
                                true
                            }

                            MotionEvent.ACTION_MOVE -> {
                                if (rightJoystickVisible) {
                                    val maxOffset: Float = (joystickSize / 4).dp.toPx()

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
                                        "$normalizedX, $normalizedY"
                                    )

                                    connectionViewModel.updateJoystickMovement(normalizedX, normalizedY)
                                }
                                true
                            }

                            MotionEvent.ACTION_UP -> {
                                rightJoystickVisible = false

                                connectionViewModel.updateJoystickMovement(0f, 0f)
                                connectionViewModel.updateIsSendingMovement(false)
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

                if (rightJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
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
    }
    */

    /*
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        with(LocalDensity.current) {
            val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
            val screenHeightDp = LocalConfiguration.current.screenHeightDp.dp

            Box(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .size(width = joystickAreaWidth * screenWidthDp, height = joystickAreaHeight * screenHeightDp)
                    .pointerInteropFilter { event ->
                        val adjustmentOffset = joystickSize / 4f

                        when (event.action) {
                            MotionEvent.ACTION_DOWN -> {
                                leftJoystickVisible = true
                                leftJoystickPosition = Offset(event.x, event.y)
                                leftDotPosition = Offset(adjustmentOffset, adjustmentOffset)

                                Log.d(
                                    "Joystick",
                                    "${leftDotPosition.x - adjustmentOffset}, ${leftDotPosition.y - adjustmentOffset}"
                                )

                                connectionViewModel.updateIsSendingMovement(true)
                                true
                            }

                            MotionEvent.ACTION_MOVE -> {
                                if (leftJoystickVisible) {
                                    val maxOffset: Float = (joystickSize / 4).dp.toPx()

                                    val x = event.x - leftJoystickPosition.x
                                    val y = event.y - leftJoystickPosition.y
                                    val distance = sqrt(x * x + y * y)
                                    val constrainedX =
                                        if (distance > maxOffset) x * (maxOffset / distance) else x
                                    val constrainedY =
                                        if (distance > maxOffset) y * (maxOffset / distance) else y
                                    leftDotPosition =
                                        Offset(constrainedX + adjustmentOffset, constrainedY + adjustmentOffset)

                                    val normalizedX = (rightDotPosition.x - adjustmentOffset) / maxOffset
                                    val normalizedY = (rightDotPosition.y - adjustmentOffset) / maxOffset

                                    Log.d(
                                        "Left Joystick ",
                                        "$normalizedX, $normalizedY"
                                    )

                                    connectionViewModel.updateLeftJoystickMovement(normalizedX, normalizedY)
                                }
                                true
                            }

                            MotionEvent.ACTION_UP -> {
                                leftJoystickVisible = false

                                connectionViewModel.updateLeftJoystickMovement(0f, 0f)

                                if (!leftJoystickVisible and !rightJoystickVisible)
                                    connectionViewModel.updateIsSendingMovement(false)
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

                if (leftJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    leftJoystickPosition.x.roundToInt() - 250,
                                    leftJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = leftDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("JoyStick", "$x, $y")
                    }
                }
            }

            Box(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .size(width = joystickAreaWidth * screenWidthDp, height = joystickAreaHeight * screenHeightDp)
                    .pointerInteropFilter { event ->
                        val adjustmentOffset = joystickSize / 4f

                        when (event.action) {
                            MotionEvent.ACTION_DOWN -> {
                                rightJoystickVisible = true
                                rightJoystickPosition = Offset(event.x, event.y)
                                rightDotPosition = Offset(adjustmentOffset, adjustmentOffset)

                                Log.d(
                                    "Joystick",
                                    "${rightDotPosition.x - adjustmentOffset}, ${rightDotPosition.y - adjustmentOffset}"
                                )

                                connectionViewModel.updateIsSendingMovement(true)
                                true
                            }

                            MotionEvent.ACTION_MOVE -> {
                                if (rightJoystickVisible) {
                                    val maxOffset: Float = (joystickSize / 4).dp.toPx()

                                    val x = event.x - rightJoystickPosition.x
                                    val y = event.y - rightJoystickPosition.y
                                    val distance = sqrt(x * x + y * y)
                                    val constrainedX =
                                        if (distance > maxOffset) x * (maxOffset / distance) else x
                                    val constrainedY =
                                        if (distance > maxOffset) y * (maxOffset / distance) else y
                                    rightDotPosition =
                                        Offset(constrainedX + adjustmentOffset, constrainedY + adjustmentOffset)

                                    val normalizedX = (rightDotPosition.x - adjustmentOffset) / maxOffset
                                    val normalizedY = (rightDotPosition.y - adjustmentOffset) / maxOffset

                                    Log.d(
                                        "Joystick",
                                        "$normalizedX, $normalizedY"
                                    )

                                    connectionViewModel.updateRightJoystickMovement(normalizedX, normalizedY)
                                }
                                true
                            }

                            MotionEvent.ACTION_UP -> {
                                rightJoystickVisible = false

                                connectionViewModel.updateRightJoystickMovement(0f, 0f)

                                if (!leftJoystickVisible and !rightJoystickVisible)
                                    connectionViewModel.updateIsSendingMovement(false)

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

                if (rightJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    rightJoystickPosition.x.roundToInt() - 250,
                                    rightJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = rightDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("JoyStick", "$x, $y")
                    }
                }
            }
        }
    }
    */

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        with(LocalDensity.current) {
            val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
            val screenHeightDp = LocalConfiguration.current.screenHeightDp.dp
            val joystickAreaWidth = 0.45f
            val joystickAreaHeight = 0.65f

            Box(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .size(
                        width = joystickAreaWidth * screenWidthDp,
                        height = joystickAreaHeight * screenHeightDp
                    )
                    .pointerInput(Unit) {
                        detectMultitouchGestures(
                            joystickSize = joystickSize,
                            setVisible = { leftJoystickVisible = it },
                            setPosition = { leftJoystickPosition = it },
                            setDotPosition = { leftDotPosition = it },
                            updateMovement = { x, y ->
                                connectionViewModel.updateLeftJoystickMovement(
                                    x,
                                    y
                                )
                            },
                            stopMovement = {
                                connectionViewModel.updateLeftJoystickMovement(
                                    0f,
                                    0f
                                )
                            },
                            joystickVisible = { leftJoystickVisible },
                            joystickPosition = { leftJoystickPosition }
                        )
                    }
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Your column content here
                }

                if (leftJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    leftJoystickPosition.x.roundToInt() - 250,
                                    leftJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = leftDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("Left Joystick", "$x, $y")
                    }
                }
            }

            Box(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .size(
                        width = joystickAreaWidth * screenWidthDp,
                        height = joystickAreaHeight * screenHeightDp
                    )
                    .pointerInput(Unit) {
                        detectMultitouchGestures(
                            joystickSize = joystickSize,
                            setVisible = { rightJoystickVisible = it },
                            setPosition = { rightJoystickPosition = it },
                            setDotPosition = { rightDotPosition = it },
                            updateMovement = { x, y ->
                                connectionViewModel.updateRightJoystickMovement(
                                    x,
                                    y
                                )
                            },
                            stopMovement = {
                                connectionViewModel.updateRightJoystickMovement(
                                    0f,
                                    0f
                                )
                            },
                            joystickVisible = { rightJoystickVisible },
                            joystickPosition = { rightJoystickPosition }
                        )
                    }
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Your column content here
                }

                if (rightJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    rightJoystickPosition.x.roundToInt() - 250,
                                    rightJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = rightDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("Right Joystick", "$x, $y")
                    }
                }
            }
        }
    }
}

suspend fun PointerInputScope.detectMultitouchGestures(
    joystickSize: Int,
    setVisible: (Boolean) -> Unit,
    setPosition: (Offset) -> Unit,
    setDotPosition: (Offset) -> Unit,
    updateMovement: (Float, Float) -> Unit,
    stopMovement: () -> Unit,
    joystickVisible: () -> Boolean,
    joystickPosition: () -> Offset,
) {
    val adjustmentOffset = joystickSize / 4f

    awaitPointerEventScope {
        while (true) {
            val event = awaitPointerEvent()

            event.changes.forEach { change ->
                when {
                    change.changedToDown() -> {
                        setVisible(true)
                        setPosition(change.position)
                        setDotPosition(Offset(adjustmentOffset, adjustmentOffset))
                    }
                    change.changedToUp() -> {
                        setVisible(false)
                        stopMovement()
                    }
                    change.positionChanged() -> {
                        if (joystickVisible()) {
                            val maxOffset: Float = (joystickSize / 4).dp.toPx()
                            val x = change.position.x - joystickPosition().x
                            val y = change.position.y - joystickPosition().y
                            val distance = sqrt(x * x + y * y)
                            val constrainedX =
                                if (distance > maxOffset) x * (maxOffset / distance) else x
                            val constrainedY =
                                if (distance > maxOffset) y * (maxOffset / distance) else y
                            setDotPosition(
                                Offset(
                                    constrainedX + adjustmentOffset,
                                    constrainedY + adjustmentOffset
                                )
                            )

                            val normalizedX = (constrainedX) / maxOffset
                            val normalizedY = (constrainedY) / maxOffset

                            updateMovement(normalizedX, normalizedY)
                        }
                    }
                }
                change.consume()
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

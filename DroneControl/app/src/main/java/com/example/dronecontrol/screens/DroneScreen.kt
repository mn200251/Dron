package com.example.dronecontrol.screens

import android.graphics.Bitmap
import android.graphics.Color.rgb
import android.graphics.Paint
import android.view.WindowManager
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.ImageBitmapConfig
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.google.ar.core.Config
import kotlinx.coroutines.delay
import kotlin.random.Random.Default.nextInt

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

//    Canvas(modifier = Modifier.fillMaxSize()) {
//        frame?.let {
//            drawImage(it, topLeft = Offset.Zero)
//        }
//    }

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

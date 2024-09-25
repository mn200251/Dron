package com.example.dronecontrol.models

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment

import androidx.compose.ui.Modifier

import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import com.example.dronecontrol.R
import kotlin.math.*


@Composable
fun DynamicJoystick(
    modifier: Modifier = Modifier,
    size: Dp = 170.dp,
    dotSize: Dp = 40.dp,
    backgroundImage: Int = R.drawable.joystick_background2,
    dotImage: Int = R.drawable.joystick_dot2,
    backgroundAlpha: Float = 0.4f, // Alpha value between 0.0 and 1.0
    dotAlpha: Float = 0.25f, // Alpha value between 0.0 and 1.0
    dotOffset: Offset = Offset(0f, 0f),
    moved: (x: Float, y: Float) -> Unit = { _, _ -> }
) {
    val backgroundPainter: Painter = painterResource(id = backgroundImage)
    val dotPainter: Painter = painterResource(id = dotImage)

    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        Image(
            painter = backgroundPainter,
            contentDescription = "JoyStickBackground",
            modifier = Modifier
                .size(size)
                .alpha(backgroundAlpha),
            contentScale = ContentScale.Crop
        )

        Box(
            modifier = Modifier
                .offset {
                    IntOffset(
                        (dotOffset.x - dotSize.toPx() / 2).roundToInt(),
                        (dotOffset.y - dotSize.toPx() / 2).roundToInt()
                    )
                }
        ) {
            Image(
                painter = dotPainter,
                contentDescription = "JoyStickDot",
                modifier = Modifier
                    .size(dotSize)
                    .alpha(dotAlpha)
            )
        }
    }
}

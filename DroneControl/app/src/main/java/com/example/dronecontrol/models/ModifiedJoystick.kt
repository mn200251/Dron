package com.example.dronecontrol.models

import android.view.MotionEvent
import androidx.compose.foundation.Image
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi

import androidx.compose.ui.Modifier

import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.input.pointer.PointerInputChange
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInParent
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import com.example.dronecontrol.R
import kotlin.math.*

/**
 * Returns the absolute value of the given number.
 * @param size Joystick size
 * @param dotSize Joystick Dot size
 * @param backgroundImage Joystick Image Drawable
 * @param dotImage Joystick Dot Image Drawable
 */

/*
@Composable
fun ModifiedJoyStick(
    modifier: Modifier = Modifier,
    size: Dp = 170.dp,
    dotSize: Dp = 40.dp,
    backgroundImage: Int = R.drawable.joystick_background2,
    backgroundAlpha: Float = 0.4f,
    dotImage: Int = R.drawable.joystick_dot2,
    dotAlpha: Float = 0.25f,
    moved: (x: Float, y: Float) -> Unit = { _, _ -> }
) {
    Box(
        modifier = modifier
            .size(size)
    ) {
        val maxRadius = with(LocalDensity.current) { (size / 2).toPx() }
        val centerX = with(LocalDensity.current) { ((size - dotSize) / 2).toPx() }
        val centerY = with(LocalDensity.current) { ((size - dotSize) / 2).toPx() }

        var offsetX by remember { mutableStateOf(centerX) }
        var offsetY by remember { mutableStateOf(centerY) }

        Image(
            painterResource(id = backgroundImage),
            "JoyStickBackground",
            modifier = Modifier.size(size),
            alpha = backgroundAlpha
        )

        Image(
            painterResource(id = dotImage),
            "JoyStickDot",
            modifier = Modifier
                .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
                .size(dotSize)
                .pointerInput(Unit) {
                    detectDragGestures(onDragEnd = {
                        offsetX = centerX
                        offsetY = centerY
                    }) { pointerInputChange: PointerInputChange, offset: Offset ->
                        val x = offsetX + offset.x - centerX
                        val y = offsetY + offset.y - centerY
                        pointerInputChange.consume()
                        val theta = atan(-y / x)
                        if ((x.pow(2)) + (y.pow(2)) > maxRadius.pow(2)) {
                            if (x > 0 && y > 0) {
                                offsetX = centerX + (maxRadius * cos(theta))
                                offsetY = centerY + (maxRadius * -sin(theta))
                            } else if (x > 0 && y < 0) {
                                offsetX = centerX + (maxRadius * cos(theta))
                                offsetY = centerY + (maxRadius * -sin(theta))
                            } else if (x < 0 && y > 0) {
                                offsetX = centerX + (maxRadius * -cos(theta))
                                offsetY = centerY + (maxRadius * sin(theta))
                            } else {
                                offsetX = centerX + (maxRadius * -cos(theta))
                                offsetY = centerY + (maxRadius * sin(theta))
                            }
                        } else {
                            offsetX += offset.x
                            offsetY += offset.y
                        }
                    }
                }
                .onGloballyPositioned { coordinates ->
                    moved(
                        coordinates.positionInParent().x - centerX,
                        -(coordinates.positionInParent().y - centerY)
                    )
                },
            alpha = dotAlpha
        )
    }
}
*/


@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun ModifiedJoyStick(
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

    val currLocalDensity = LocalDensity.current

    Box(
        modifier = modifier/*.pointerInteropFilter { event ->
            when (event.action) {
                MotionEvent.ACTION_MOVE -> {
                    with(currLocalDensity) {
                        val x = (event.x - size.toPx() / 2) / size.toPx()
                        val y = (event.y - size.toPx() / 2) / size.toPx()
                        moved(x, y)
                    }
                    true
                }

                else -> false
            }
        },*/,
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
        /*
        Image(
            painter = dotPainter,
            contentDescription = "JoyStickDot",
            modifier = Modifier
                .size(dotSize)
                .alpha(dotAlpha)
        )
        */
    }
}

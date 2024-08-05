package com.example.dronecontrol.models

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.dronecontrol.viewmodels.Video

@Composable
fun VideoItem(video: Video) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(modifier = Modifier.padding(8.dp)) {
            video.thumbnail?.let {
                Image(
                    bitmap = it.asImageBitmap(),
                    contentDescription = "Video Thumbnail",
                    modifier = Modifier
                        .size(64.dp)
                        .clip(RoundedCornerShape(4.dp))
                )
            }
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = video.filename,
                fontSize = 18.sp,
                modifier = Modifier
                    .align(alignment = androidx.compose.ui.Alignment.CenterVertically)
            )
        }
    }
}

package com.example.dronecontrol.models

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.DialogProperties
import com.example.dronecontrol.viewmodels.Video

@Composable
fun VideoItem(video: Video, onDownloadConfirm: (Video) -> Unit) {
    var showDialog by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(containerColor = Color.DarkGray)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                // Video Thumbnail
                video.thumbnail?.let {
                    Image(
                        bitmap = it.asImageBitmap(),
                        contentDescription = "Video Thumbnail",
                        modifier = Modifier
                            .size(64.dp)
                            .clip(MaterialTheme.shapes.small)
                    )
                }

                Spacer(modifier = Modifier.width(16.dp))

                // Video Filename
                Text(
                    text = video.filename,
                    fontSize = 18.sp,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            }

            // Download Button
//            Button(onClick = { showDialog = true }) {
//                Text("Download")
//            }

            // Download Button (Green)
            Button(
                onClick = { showDialog = true },
                colors = ButtonDefaults.buttonColors(
                    // containerColor = Color.Green
                    containerColor = Color(0, 102, 0)
                ),
                shape = RoundedCornerShape(8.dp), // Rounded corners for a better look
                modifier = Modifier.padding(4.dp) // Padding around the button
            ) {
                Text("Download", color = Color.White)
            }

            // Rename Button (Blue)
            Button(
                onClick = { /* Handle rename action */ },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Blue
                ),
                shape = RoundedCornerShape(8.dp), // Rounded corners for a better look
                modifier = Modifier.padding(4.dp) // Padding around the button
            ) {
                Text("Rename", color = Color.White)
            }

            // Delete Button (Red)
            Button(
                onClick = { /* Handle delete action */ },
                colors = ButtonDefaults.buttonColors(
                    // containerColor = Color.Red
                    containerColor = Color(128, 0, 0)
                ),
                shape = RoundedCornerShape(8.dp), // Rounded corners for a better look
                modifier = Modifier.padding(4.dp) // Padding around the button
            ) {
                Text("Delete", color = Color.White)
            }

            if (showDialog) {
                AlertDialog(
                    onDismissRequest = { showDialog = false },
                    title = { Text(text = "Download Video", color = Color.White) },
                    text = { Text(text = "Do you wish to download video ${video.filename}?", color = Color.White) },
                    confirmButton = {
                        Button(onClick = {
                            showDialog = false
                            onDownloadConfirm(video)
                        }) {
                            Text("Yes")
                        }
                    },
                    dismissButton = {
                        Button(onClick = { showDialog = false }) {
                            Text("No")
                        }
                    },
                    containerColor = Color.DarkGray,
                    properties = DialogProperties()
                )
            }
        }
    }
}

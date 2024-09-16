package com.example.dronecontrol.models

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import kotlin.math.sin

@Composable
fun VideoItem(video: Video,
              onDownloadConfirm: (Video) -> Unit,
              onRenameConfirm: (String, String) -> Unit,
              onDeleteConfirm: (Video) -> Unit
)
{
    var showDownloadDialog by remember { mutableStateOf(false) }
    var isRenaming by remember { mutableStateOf(false) }
    var showDeleteDialog by remember { mutableStateOf(false) }

    var newName: String by remember { mutableStateOf(video.filename) }

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

                OutlinedTextField(value = newName,
                    onValueChange = { it ->
                        newName = it
                    },
                    readOnly = !isRenaming,
                    singleLine = true
                )
            }

            // Download Button
//            Button(onClick = { showDialog = true }) {
//                Text("Download")
//            }


            Button(
                onClick = { showDownloadDialog = true },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0, 102, 0)
                ),
                enabled = !isRenaming,
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.padding(4.dp)
            ) {
                Text("Download", color = Color.White)
            }

            Button(
                onClick = {
                    if (isRenaming)
                    {
                        onRenameConfirm(video.filename, newName)
                    }
                    else
                    {

                    }

                    isRenaming = isRenaming.not()
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Blue
                ),
                shape = RoundedCornerShape(8.dp),
                enabled = video.filename.isNotEmpty(),
                modifier = Modifier.padding(4.dp)
            ) {
                if (isRenaming)
                    Text("Save", color = Color.White)
                else
                    Text("Rename", color = Color.White)
            }

            Button(
                onClick = { showDeleteDialog = true },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(128, 0, 0)
                ),
                enabled = !isRenaming,
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.padding(4.dp)
            ) {
                Text("Delete", color = Color.White)
            }

            if (showDownloadDialog) {
                AlertDialog(
                    onDismissRequest = { showDownloadDialog = false },
                    title = { Text(text = "Download Video", color = Color.White) },
                    text = { Text(text = "Do you wish to download video ${video.filename}?", color = Color.White) },
                    confirmButton = {
                        Button(onClick = {
                            showDownloadDialog = false
                            onDownloadConfirm(video)
                        }) {
                            Text("Yes")
                        }
                    },
                    dismissButton = {
                        Button(onClick = { showDownloadDialog = false }) {
                            Text("No")
                        }
                    },
                    containerColor = Color.DarkGray,
                    properties = DialogProperties()
                )
            }

            if (showDeleteDialog) {
                AlertDialog(
                    onDismissRequest = { showDeleteDialog = false },
                    title = { Text(text = "Delete Video", color = Color.White) },
                    text = { Text(text = "Do you wish to delete this video ${video.filename}?", color = Color.White) },
                    confirmButton = {
                        Button(onClick = {
                            showDeleteDialog = false

                            onDeleteConfirm(video)
                        }) {
                            Text("Yes")
                        }
                    },
                    dismissButton = {
                        Button(onClick = { showDeleteDialog = false }) {
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

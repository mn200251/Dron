package com.example.dronecontrol.utils

import android.os.Build
import android.util.Log
import androidx.annotation.RequiresApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.kohsuke.github.GHRepository
import org.kohsuke.github.GitHubBuilder
import java.io.InputStream
import kotlin.io.encoding.ExperimentalEncodingApi

@RequiresApi(Build.VERSION_CODES.O)
suspend fun getCurrentIP(githubToken: String, repoName: String, filePath: String, branchName: String): Pair<String, String>? {
    return withContext(Dispatchers.IO) {
        try {
            val github = GitHubBuilder().withOAuthToken(githubToken).build()

            val repo: GHRepository = github.getRepository(repoName)

            val file = repo.getFileContent(filePath, branchName)
            val inputStream: InputStream = file.read()
            val decodedContent = inputStream.readBytes().toString(Charsets.UTF_8).trim()

            Log.d("decodedContent", decodedContent)

            // Split the IP address and port
            val parts = decodedContent.split(":")

            if (parts.size == 2) {
                val ip = parts[0].trim()

                var port = parts[1].trim()
                try {
                    val portTest = parts[1].trim().toInt()
                }
                catch(e: NumberFormatException) {
                    println("Port is not type int!")
                    return@withContext null
                }
                return@withContext Pair(ip, port)
            } else {
                println("The content format is incorrect.")
                return@withContext null
            }
        } catch (e: Exception) {
            println("An error occurred: ${e.message}")
            return@withContext null
        }
    }
}
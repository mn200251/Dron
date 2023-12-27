package com.example.phonedelaytest.retrofit

import com.google.gson.JsonDeserializationContext
import com.google.gson.JsonDeserializer
import com.google.gson.JsonElement
import retrofit2.Retrofit
import retrofit2.converter.scalars.ScalarsConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import java.lang.reflect.Type
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class LocalDateTimeDeserializer : JsonDeserializer<LocalDateTime> {

    override fun deserialize(
        json: JsonElement?,
        typeOfT: Type?,
        context: JsonDeserializationContext?
    ): LocalDateTime {
        val dateTimeString = json?.asString
        val formatter = DateTimeFormatter.ISO_DATE_TIME
        return LocalDateTime.parse(dateTimeString, formatter)
    }
}


interface ApiService {
    @GET("fetchData/")
    suspend fun fetchData(): String

    @GET("sendData/")
    suspend fun sendData(@Body s: ByteArray)
}

class RetrofitClient(
    private val apiService: ApiService
)
{
    companion object {
        val BASE_URL = "https://178.148.72.53:6969/"

        fun create(): ApiService? {
            val retrofit = Retrofit.Builder()
                .baseUrl(BASE_URL)
                .addConverterFactory(ScalarsConverterFactory.create())
                .build()

            return retrofit.create(ApiService::class.java)
        }
    }

    suspend fun fetchData(): String{
        return apiService.fetchData()
    }

    suspend fun sendData(s: ByteArray){
        return apiService.sendData(s)

    }
}
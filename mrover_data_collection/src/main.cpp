#define ENABLE_USER_AUTH
#define ENABLE_DATABASE
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <FirebaseClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);// Network and Firebase credentials
#define WIFI_SSID "Lucas Iphone"
#define WIFI_PASSWORD "12345678"
#define Web_API_KEY "AIzaSyCgG9kg3N50gPSCHtGKO5bU_v8zRs7wqBE"
#define DATABASE_URL "https://mrover-drone-example-default-rtdb.firebaseio.com/"
#define USER_EMAIL "luca.hardi.26@gmail.com"
#define USER_PASS "12345678"// User function
void processData(AsyncResult &aResult);// Authentication
UserAuth user_auth(Web_API_KEY, USER_EMAIL, USER_PASS);// Firebase components
FirebaseApp app;
WiFiClientSecure ssl_client;
using AsyncClient = AsyncClientClass;
AsyncClient aClient(ssl_client);
RealtimeDatabase Database;// Timer variables for sending data every 10 seconds
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 1000; // 10 seconds in milliseconds// Variables to send to the database
int intValue = 0;
float floatValue = 0.01;
String stringValue = "";void setup(){
  Serial.begin(115200);  // Connect to Wi-Fi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println();  Serial.println("");  if(!accel.begin()) {
    Serial.println("Ooops, no ADXL345 detected ... Check your wiring!");
    while(1);
  }  accel.setRange(ADXL345_RANGE_16_G);
  // Configure SSL client
  ssl_client.setInsecure();
  // ssl_client.setConnectionTimeout(1000);
  ssl_client.setHandshakeTimeout(5);  // Initialize Firebase
  initializeApp(aClient, app, getAuth(user_auth), processData, ":closed_lock_with_key: authTask");
  app.getApp<RealtimeDatabase>(Database);
  Database.url(DATABASE_URL);
}void loop(){
    sensors_event_t event;
  accel.getEvent(&event);  // Maintain authentication and async tasks
  app.loop();
  // Check if authentication is ready
  if (app.ready()){
    // Periodic data sending every 10 seconds
    unsigned long currentTime = millis();
    if (currentTime - lastSendTime >= sendInterval){
      // Update the last send time
      lastSendTime = currentTime;      Database.set<float>(aClient, "/Acceleration/X", event.acceleration.x, processData, "RTDB_Send_X_Accel");
      Database.set<float>(aClient, "/Acceleration/Y", event.acceleration.y, processData, "RTDB_Send_Y_Accel");
      Database.set<float>(aClient, "/Acceleration/Z", event.acceleration.z, processData, "RTDB_Send_Z_Accel");    }
  }
}void processData(AsyncResult &aResult) {
  if (!aResult.isResult())
    return;  if (aResult.isEvent())
    Firebase.printf("Event task: %s, msg: %s, code: %d\n", aResult.uid().c_str(), aResult.eventLog().message().c_str(), aResult.eventLog().code());  if (aResult.isDebug())
    Firebase.printf("Debug task: %s, msg: %s\n", aResult.uid().c_str(), aResult.debug().c_str());  if (aResult.isError())
    Firebase.printf("Error task: %s, msg: %s, code: %d\n", aResult.uid().c_str(), aResult.error().message().c_str(), aResult.error().code());  if (aResult.available())
    Firebase.printf("task: %s, payload: %s\n", aResult.uid().c_str(), aResult.c_str());
}
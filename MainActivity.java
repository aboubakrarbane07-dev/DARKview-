package com.darkocut.myapp;

import android.app.Activity;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.CheckBox;
import android.widget.Toast;
import com.darkocut.myapp.R;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {

    // عناصر شاشة تسجيل الدخول
    private EditText etUsername;
    private EditText etPassword;
    private Button btnLogin;

    // عناصر شاشة المستخدم (الزبون)
    private CheckBox chkHair;
    private CheckBox chkBeard;
    private Button btnConfirmBooking;

    private String currentLoggedInUser = "Guest";
    
    // سطر الرابط الخاص بقاعدة بيانات Firebase (استبدل YOUR_PROJECT_ID برمز مشروعك الفعلي)
    private final String FIREBASE_URL = "https://darkocut-default-rtdb.firebaseio.com/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // تشغيل شاشة تسجيل الدخول أولاً عند فتح التطبيق
        loadLoginScreen();
    }

    // دالة لتحميل وبرمجة شاشة تسجيل الدخول بالصلاحيات الجديدة
    private void loadLoginScreen() {
        setContentView(R.layout.login_panel);

        etUsername = (EditText) findViewById(R.id.etUsername);
        etPassword = (EditText) findViewById(R.id.etPassword);
        btnLogin = (Button) findViewById(R.id.btnLogin);

        btnLogin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String username = etUsername.getText().toString().trim();
                String password = etPassword.getText().toString().trim();

                // التحقق من الحقول الفارغة
                if (username.isEmpty() || password.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please enter username and password", Toast.LENGTH_SHORT).show();
                    return;
                }

                currentLoggedInUser = username; // حفظ اسم المستخدم الحالي للحجز السحابي

                // 1. التحقق إذا كان الحساب للمطور ببياناته المحدثة
                if (username.equals("developer") && password.equals("developer22")) {
                    setContentView(R.layout.admin_panel);
                    Toast.makeText(MainActivity.this, "Welcome Creator!", Toast.LENGTH_SHORT).show();
                } 
                // 2. التحقق إذا كان الحساب للحلاق بكلمة المرور المحدثة
                else if (username.equals("barber") && password.equals("22102002Hk")) {
                    setContentView(R.layout.barber_panel);
                    Toast.makeText(MainActivity.this, "Welcome Barber!", Toast.LENGTH_SHORT).show();
                } 
                // 3. أي حساب آخر يعتبر زبون/مستخدم عادي ويفتح واجهة الحجز السحابية
                else {
                    loadUserPanel();
                    Toast.makeText(MainActivity.this, "Welcome " + username, Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    // دالة تحميل واجهة حجز المستخدم وإرسال البيانات للسيرفر
    private void loadUserPanel() {
        setContentView(R.layout.user_panel);

        chkHair = (CheckBox) findViewById(R.id.chkHair);
        chkBeard = (CheckBox) findViewById(R.id.chkBeard);
        btnConfirmBooking = (Button) findViewById(R.id.btnConfirmBooking);

        btnConfirmBooking.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String serviceType = "";
                if (chkHair.isChecked()) serviceType += "Haircut ";
                if (chkBeard.isChecked()) serviceType += "BeardShave";

                if (serviceType.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please select at least one service", Toast.LENGTH_SHORT).show();
                    return;
                }

                // تجهيز نص البيانات بصيغة JSON لإرسالها سحابياً
                String jsonPayload = "{"
                        + "\"customerName\":\"" + currentLoggedInUser + "\","
                        + "\"services\":\"" + serviceType + "\","
                        + "\"status\":\"Pending\""
                        + "}";

                // تشغيل مهمة الإرسال في الخلفية عبر الإنترنت
                new SendBookingTask().execute(jsonPayload);
            }
        });
    }

    // كائن برمجى لإرسال البيانات عبر الـ Internet في الخلفية (Background Thread)
    private class SendBookingTask extends AsyncTask<String, Void, Boolean> {
        @Override
        protected Boolean doInBackground(String... params) {
            try {
                URL url = new URL(FIREBASE_URL);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                conn.setDoOutput(true);

                OutputStream os = conn.getOutputStream();
                os.write(params[0].getBytes("UTF-8"));
                os.close();

                int responseCode = conn.getResponseCode();
                return responseCode == HttpURLConnection.HTTP_OK || responseCode == 201;
            } catch (Exception e) {
                e.printStackTrace();
                return false;
            }
        }

        @Override
        protected void onPostExecute(Boolean success) {
            if (success) {
                Toast.makeText(MainActivity.this, "Sent to Barber Cloud successfully!", Toast.LENGTH_LONG).show();
            } else {
                Toast.makeText(MainActivity.this, "Connection Error! Check internet.", Toast.LENGTH_LONG).show();
            }
        }
    }

    // عند الضغط على زر الرجوع في الهاتف، يعود لشاشة تسجيل الدخول
    @Override
    public void onBackPressed() {
        loadLoginScreen();
    }
}

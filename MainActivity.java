package com.darkocut.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import com.darkocut.myapp.R;

public class MainActivity extends Activity {

    // عناصر شاشة تسجيل الدخول
    private EditText etUsername;
    private EditText etPassword;
    private Button btnLogin;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // تشغيل شاشة تسجيل الدخول أولاً عند فتح التطبيق
        loadLoginScreen();
    }

    // دالة لتحميل وبرمجة شاشة تسجيل الدخول
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

                // 1. التحقق إذا كان الحساب للمطور (أنت)
                if (username.equals("developer") && password.equals("developer22")) {
                    setContentView(R.layout.admin_panel);
                    Toast.makeText(MainActivity.this, "Welcome Creator!", Toast.LENGTH_SHORT).show();
                } 
                // 2. التحقق إذا كان الحساب للحلاق
                else if (username.equals("barber") && password.equals("22102002Hk")) {
                    setContentView(R.layout.barber_panel);
                    Toast.makeText(MainActivity.this, "Welcome Barber!", Toast.LENGTH_SHORT).show();
                } 
                // 3. أي حساب آخر يعتبر زبون/مستخدم عادي
                else {
                    setContentView(R.layout.user_panel);
                    Toast.makeText(MainActivity.this, "Welcome " + username, Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    // عند الضغط على زر الرجوع في الهاتف، يعود لشاشة تسجيل الدخول
    @Override
    public void onBackPressed() {
        loadLoginScreen();
    }
}

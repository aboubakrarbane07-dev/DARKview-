package com.darkocut.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;
import com.darkocut.myapp.R;

public class MainActivity extends Activity {

    private Button btnUserPanel;
    private Button btnBarberPanel;
    private Button btnAdminPanel;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // ابدأ بالواجهة الرئيسية التي تحتوي على الأزرار الثلاثة
        setContentView(R.layout.main);

        // ربط الأزرار من الواجهة
        btnUserPanel = (Button) findViewById(R.id.btnUserPanel);
        btnBarberPanel = (Button) findViewById(R.id.btnBarberPanel);
        btnAdminPanel = (Button) findViewById(R.id.btnAdminPanel);

        // 1. عند الضغط على زر المستخدم
        btnUserPanel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                setContentView(R.layout.user_panel);
                Toast.makeText(MainActivity.this, "Welcome Customer", Toast.LENGTH_SHORT).show();
            }
        });

        // 2. عند الضغط على زر الحلاق
        btnBarberPanel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                setContentView(R.layout.barber_panel);
                Toast.makeText(MainActivity.this, "Welcome Barber", Toast.LENGTH_SHORT).show();
            }
        });

        // 3. عند الضغط على زر المطور (أنت صانع التطبيق)
        btnAdminPanel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                setContentView(R.layout.admin_panel);
                Toast.makeText(MainActivity.this, "Accessing Developer Console...", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // ميزة برمجية: عند الضغط على زر الرجوع في الهاتف، يعود للوحة التحكم الرئيسية بدلاً من إغلاق التطبيق
    @Override
    public void onBackPressed() {
        setContentView(R.layout.main);
        // إعادة ربط الأزرار لأننا قمنا بتغيير الواجهة
        btnUserPanel = (Button) findViewById(R.id.btnUserPanel);
        btnBarberPanel = (Button) findViewById(R.id.btnBarberPanel);
        btnAdminPanel = (Button) findViewById(R.id.btnAdminPanel);
    }
}

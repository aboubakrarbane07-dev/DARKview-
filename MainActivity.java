package com.darkocut.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;
import com.darkocut.myapp.R;

public class MainActivity extends Activity {

    private Button btnBook;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        btnBook = (Button) findViewById(R.id.btnBook);

        btnBook.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(MainActivity.this, "Opening appointment page...", Toast.LENGTH_SHORT).show();
            }
        });
    }
}

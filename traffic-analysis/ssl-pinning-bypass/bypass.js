/*
    Frida SSL Pinning Bypass
*/

if (Java.available) {
    Java.perform(function() {
        console.log("Loading SSL pinning bypass hooks...");

        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        
        var TrustManager = Java.registerClass({
            name: 'com.sandbox.TrustManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });

        var TrustManagers = [TrustManager.$new()];

        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        SSLContext.init.overload(
            '[Ljavax.net.ssl.KeyManager;', 
            '[Ljavax.net.ssl.TrustManager;', 
            'java.security.SecureRandom'
        ).implementation = function(keyManager, trustManager, secureRandom) {
            console.log("Bypassing SSLContext.init");
            return this.init(keyManager, TrustManagers, secureRandom);
        };

        try {
            var CertificatePinner = Java.use('okhttp3.CertificatePinner');
            CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {
                console.log("Bypassing OkHttp3 CertificatePinner for " + hostname);
                return;
            };
        } catch (err) {
            // okhttp3 not in use or obfuscated
        }

        try {
            TrustManagerImpl.checkServerTrusted.overload(
                '[Ljava.security.cert.X509Certificate;', 
                'java.lang.String', 
                'java.lang.String'
            ).implementation = function(chain, authType, host) {
                console.log("Bypassing conscious trust check for: " + host);
                return chain;
            };
        } catch (err) {
            // TrustManagerImpl not found
        }

        try {
            var WebViewClient = Java.use('android.webkit.WebViewClient');
            WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
                console.log("Bypassing WebView SSL error");
                handler.proceed();
            };
        } catch (err) {
            // WebView not in use
        }
    });
} else {
    console.log("Java VM not available");
}

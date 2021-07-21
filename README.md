# redis_proxy_for_phantom

<H3> <a href="https://mitmproxy.org/">mitmproxy</a> 만들기 </H3>

<br/>
1. Redis Libarary 추가를 위해서 소스 빌드하기
<div>
  외부 모듈(redis)를 import 하기 위해서는 mitmproxy 소스를 받아서 새로 빌드해야 합니다. 
  빌드를 위해서는 python 3.8 이상이 필요합니다. 
  <pre>
$ mkdir mitmproxy_dev
$ cd mitmproxy_dev/
$ python3 -m venv  ./
$ source bin/activate
$ git clone https://github.com/mitmproxy/mitmproxy.git
$ cd mitmproxy/
$ pip install --upgrade pip
$ pip install pipx
$ pip install mitmproxy
$ pip install redis  
$ pipx inject mitmproxy redis # Redis library 를 mitmproxy 프로젝트에 추가
$ pip install -e ".[dev]"  
  </pre>
</dv>
<br/>
2. Request Intercept 하는 add-on 만들기 
<div>
  http-reply-from-proxy.py 소스 참조
</div>
<br/>
3. Proxy 실행 하기 (내부에 있는 서버에서)
<div>
  <pre>
  $ mitmproxy --set block_global=false -s ~/addon/http-reply-from-proxy.py
  </pre>
</div>
<br/>
4. mitmproxy CA Cert를 Phantom에 등록하기
<div>
  1) Proxy server에서 해당 내용 복사  
  <pre>
  $ cat ~/.mitmproxy/mitmproxy-ca-cert.cer
  </pre>
  2) Phantom 서버에서 복사 된 내용 등록
  <pre>
  $ cat > mitmproxy-ca.crt
  (복사한 내용 붙여넣기)
  ^D
  $ sudo phenv python3 /opt/phantom/bin/import_cert.py -i ./mitmproxy-ca.crt
  $ sudo $PHANTOM_HOME/bin/phsvc restart uwsgi
  </pre>
</div>
<br/>
5. Phantom Assert 설정
<div>
![image](https://user-images.githubusercontent.com/3444089/126444827-0149470a-6a68-499c-a7ae-cc910c3a4e74.png)
</div>

  
<H3> 외부접속 Proxy 만들기 </H3>

1. 외부 접속 수행하는 Worker 만들기 <- 나중에 daemon 으로 만들어야 함
<div>
  redis-worker.py 소스 참조
</div>
<br/>

2. Worker 실행 
<p>
  서버실행 : python redis-worker.py 
</p>

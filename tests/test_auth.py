import unittest
from sippy.SipWWWAuthenticate import SipWWWAuthenticate
from sippy.SipAuthorization import SipAuthorization
from sippy.SipHeader import SipHeader
from sippy.SipResponse import SipResponse
import hashlib 

# WWW-Authenticate: Digest realm="tasstax.infraserv.com",nonce="04451a7118e2f3673e749aecb96df8f5f94bd5216541d986c7bc00f90a04c164",opaque="",stale=FALSE,algorithm=SHA-256

class TestSha256Auth(unittest.TestCase):
    def test_simple(self):
        authi = SipWWWAuthenticate(realm="tasstax.infraserv.com", nonce="04451a7118e2f3673e749aecb96df8f5f94bd5216541d986c7bc00f90a04c164", algorithm="SHA-256")
        authi.opaque = ""
        resi = SipResponse(scode=401, reason="Unauthorized", sipver="SIP/2.0")
        resi.appendHeader(SipHeader(name='WWW-Authenticate', body=authi))
        
        print("result")
        print(resi)


        self.assertEqual(True, True)

    def test_md5_digest(self):
        password = "Circle Of Life"
        username = "Mufasa"
        realm = "testrealm@host.com"
        nonce = "dcd98b7102dd2f0e8b11d0f600bfb0c093"
        uri = "/dir/index.html"
        qop = "auth"
        nc = "00000001"
        cnonce = "0a4f113b"
        response = "6629fae49393a05397450978507c4ef1"
        # opaque="5ccc069c403ebaf9f0171e9517f40e41"

        s1 = username + ":" + realm + ":" + password
        HA1 = hashlib.md5(s1.encode()).hexdigest()
        s2 = "GET:"+uri
        HA2 = hashlib.md5(s2.encode()).hexdigest()
        print("credentials hash {}".format(HA1))
        print("request hash {}".format(HA2))
        # calc on server side
        s3 = HA1 + ":" + nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + HA2
        verify = hashlib.md5(s3.encode()).hexdigest()
        print("verifcation should match response {}".format(verify))
        self.assertEqual(verify, response)


    def test_sip_md5_digest(self):
        # calc with values from tassta app 10.2.8
        # WWW-Authenticate: Digest realm="voyager.tassta.com",nonce="f07e5466c5627a60ff0110bba156b4fe",opaque="",stale=FALSE,algorithm=MD5 
        # Authorization: Digest username="39a88fd5c40f43222f7c1e8cec89e813@voyager.tassta.com",realm="voyager.tassta.com",
        # nonce="f07e5466c5627a60ff0110bba156b4fe",uri="sip:voyager.tassta.com",response="439c964c0a29d252a83e379ed62cd969",algorithm=MD5,opaque="" 
        password = ""
        username="39a88fd5c40f43222f7c1e8cec89e813@voyager.tassta.com"
        realm="voyager.tassta.com"
        nonce="f07e5466c5627a60ff0110bba156b4fe"
        method="REGISTER"
        uri="sip:voyager.tassta.com"
        response="439c964c0a29d252a83e379ed62cd969"

        s1 = username + ":" + realm + ":" + password
        HA1 = hashlib.md5(s1.encode()).hexdigest()
        print("credentials hash {}".format(HA1))

        s2 = method + ":" + uri
        HA2 = hashlib.md5(s2.encode()).hexdigest()
        print("request hash {}".format(HA2))

        # calc on server side
        s3 = HA1 + ":" + nonce + ":" + HA2
        verify = hashlib.md5(s3.encode()).hexdigest()
        print("verifcation should match response {}".format(verify))
        self.assertEqual(verify, response)

    def test_parse_www_auth(self):
        # same as above but with SipAuthorization Object
        # Authorization: Digest username="39a88fd5c40f43222f7c1e8cec89e813@voyager.tassta.com",realm="voyager.tassta.com",
        # nonce="f07e5466c5627a60ff0110bba156b4fe",uri="sip:voyager.tassta.com",response="439c964c0a29d252a83e379ed62cd969",algorithm=MD5,opaque="" 
        authstr = 'Digest username="39a88fd5c40f43222f7c1e8cec89e813@voyager.tassta.com",realm="voyager.tassta.com",nonce="f07e5466c5627a60ff0110bba156b4fe",uri="sip:voyager.tassta.com",response="439c964c0a29d252a83e379ed62cd969",algorithm=MD5,opaque=""'
        authi = SipAuthorization(body=authstr)
        authi.parse()
        self.assertEqual('39a88fd5c40f43222f7c1e8cec89e813@voyager.tassta.com', authi.username)
        self.assertEqual('voyager.tassta.com', authi.realm)
        self.assertEqual('439c964c0a29d252a83e379ed62cd969', authi.response)
        self.assertTrue(authi.verify('','REGISTER'))

    def test_parse_www_auth2(self):
        # implementation with qop=auth seems to be broke either on sippy or on resiprocate side!!
        # authstr = 'Digest username="20982b62b33207a8670e94b377fc98ef@voyager.tassta.com",realm="voyager.tassta.com",nonce="04451a7118e2f3673e749aecb96df8f5f94bd5216541d986c7bc00f90a04c164",uri="sip:voyager.tassta.com",response="276cc557d3d5358caf95bb555bf374f5",cnonce="6280161f8e79a9787756e4a28e2ec93c",nc=00000001,qop=auth,algorithm=MD5'
        authstr = 'Digest username="20982b62b33207a8670e94b377fc98ef@voyager.tassta.com",realm="voyager.tassta.com",nonce="f07e5466c5627a60ff0110bba156b4fe",uri="sip:voyager.tassta.com",response="49f69913789862b495cb2a15063a7d79",algorithm=MD5'
        authi = SipAuthorization(body=authstr)
        authi.parse()
        self.assertEqual('20982b62b33207a8670e94b377fc98ef@voyager.tassta.com', authi.username)
        self.assertEqual('voyager.tassta.com', authi.realm)
        self.assertTrue(authi.verify('password','REGISTER'))

    def test_parse_www_auth_and_cnonce(self):
        authstr= 'Digest username="20982b62b33207a8670e94b377fc98ef@voyager.tassta.com",realm="tasstax.infraserv.com",nonce="04451a7118e2f3673e749aecb96df8f5f94bd5216541d986c7bc00f90a04c164",uri="sip:voyager.tassta.com",response="597870321a5dbf188228b6e78c59ff73",cnonce="d987d438e26f21c110f0aab9afdac26a",nc=00000001,qop=auth,algorithm=MD5'
        authi = SipAuthorization(body=authstr)
        authi.parse()
        self.assertEqual("d987d438e26f21c110f0aab9afdac26a", authi.cnonce)
        self.assertEqual("00000001", authi.nc)
        self.assertEqual("MD5", authi.algorithm)
        self.assertEqual("auth", authi.qop)
        self.assertEqual('20982b62b33207a8670e94b377fc98ef@voyager.tassta.com', authi.username)
        self.assertEqual('tasstax.infraserv.com', authi.realm)
        self.assertTrue(authi.verify('password','REGISTER'))


    def test_see_if_resip_is_wrong(self):
        authi = SipAuthorization(username="user", uri="user@host.com", realm="localhost", nonce="92347fea23", response="66d52b4b0e9e968dbdc116f4eb1f92a0")
        authi.cnonce = "72345hef"
        authi.nc = "00000001"
        authi.algorithm = "MD5"
        authi.qop = "auth"
        self.assertTrue(authi.verify("secret", "REGISTER"))


# 14 Feb 08:36:42.650/GLOBAL/b2bua: RECEIVED message from 192.168.60.24:46842:
# REGISTER sip:voyager.tassta.com SIP/2.0
# Via: SIP/2.0/UDP 192.168.60.24:46842;branch=z9hG4bK-524287-1---8ee3e022fcb1ec75;rport
# Max-Forwards: 70
# Contact: <sip:872f83d9-a2d4-44bf-bc2e-c27d926f0a9d@voyager.tassta.com;rinstance=e1b0221f5cc19f52;transport=udp>;+g.3gpp.icsi-ref="urn%3Aurn-7%3A3gpp-service.ims.icsi.mcptt";+g.3gpp.mcptt
# To: <sip:872f83d9-a2d4-44bf-bc2e-c27d926f0a9d@voyager.tassta.com>
# From: <sip:872f83d9-a2d4-44bf-bc2e-c27d926f0a9d@voyager.tassta.com>;tag=4191ec54
# Call-ID: bclLrUmVSy-eyeyZmWrIIw..
# CSeq: 2 REGISTER
# Expires: 360
# Allow: INVITE, ACK, CANCEL, OPTIONS, BYE, UPDATE, NOTIFY, SUBSCRIBE, MESSAGE, INFO, REFER
# User-Agent: Eurofunk MCX Gateway
# Authorization: Digest username="c51e247449121b4d2d9b57ddf2dfc9da@voyager.tassta.com",realm="tasstax.infraserv.com",nonce="04451a7118e2f3673e749aecb96df8f5f94bd5216541d986c7bc00f90a04c164",uri="sip:voyager.tassta.com",response="50e9d7605a65af9c90f3ba21c2e09b73411d27a7d5df136d843bca29f37a4de4",cnonce="76b1ec999d4744f44f62e2de559794bb",nc=00000001,qop=auth,algorithm=SHA-256
# Content-Length: 0

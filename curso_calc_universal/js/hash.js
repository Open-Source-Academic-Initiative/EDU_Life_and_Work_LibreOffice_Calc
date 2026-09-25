/*
 * SHA-256 and MD5 over bytes (Uint8Array), pure JavaScript.
 * Used to fingerprint the certificate PDF so the campus can verify that a
 * file was not altered. Synchronous and dependency-free on purpose: it also
 * works offline and outside secure contexts (file://), unlike crypto.subtle.
 */
(function (root) {
  "use strict";

  function hex(words, littleEndian) {
    var out = "";
    words.forEach(function (w) {
      for (var i = 0; i < 4; i++) {
        var b = littleEndian ? (w >>> (8 * i)) & 255 : (w >>> (24 - 8 * i)) & 255;
        out += (b < 16 ? "0" : "") + b.toString(16);
      }
    });
    return out;
  }

  // ------------------------------------------------------------- SHA-256
  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function pad(bytes, bigEndianLength) {
    var len = bytes.length, bitLen = len * 8;
    var total = ((len + 9 + 63) >> 6) << 6;
    var buf = new Uint8Array(total);
    buf.set(bytes);
    buf[len] = 0x80;
    var hi = Math.floor(bitLen / 0x100000000), lo = bitLen >>> 0;
    for (var i = 0; i < 4; i++) {
      if (bigEndianLength) {
        buf[total - 1 - i] = (lo >>> (8 * i)) & 255;
        buf[total - 5 - i] = (hi >>> (8 * i)) & 255;
      } else {
        buf[total - 8 + i] = (lo >>> (8 * i)) & 255;
        buf[total - 4 + i] = (hi >>> (8 * i)) & 255;
      }
    }
    return buf;
  }

  function sha256(bytes) {
    var buf = pad(bytes, true);
    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var w = new Array(64);
    for (var off = 0; off < buf.length; off += 64) {
      for (var t = 0; t < 16; t++) {
        var j = off + t * 4;
        w[t] = (buf[j] << 24) | (buf[j + 1] << 16) | (buf[j + 2] << 8) | buf[j + 3];
      }
      for (t = 16; t < 64; t++) {
        var x = w[t - 15], y = w[t - 2];
        var s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3);
        var s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (t = 0; t < 64; t++) {
        var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
        var ch = (e & f) ^ (~e & g);
        var t1 = (h + S1 + ch + K[t] + w[t]) | 0;
        var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
      H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
    }
    return hex(H, false);
  }

  // ----------------------------------------------------------------- MD5
  var S = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
           5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
           4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
           6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21];
  var T = [];
  for (var i = 0; i < 64; i++) T[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 0x100000000) | 0;

  function md5(bytes) {
    var buf = pad(bytes, false);
    var a0 = 0x67452301, b0 = 0xefcdab89 | 0, c0 = 0x98badcfe | 0, d0 = 0x10325476;
    var m = new Array(16);
    for (var off = 0; off < buf.length; off += 64) {
      for (var k = 0; k < 16; k++) {
        var j = off + k * 4;
        m[k] = buf[j] | (buf[j + 1] << 8) | (buf[j + 2] << 16) | (buf[j + 3] << 24);
      }
      var A = a0, B = b0, C = c0, D = d0;
      for (var n = 0; n < 64; n++) {
        var F, g;
        if (n < 16) { F = (B & C) | (~B & D); g = n; }
        else if (n < 32) { F = (D & B) | (~D & C); g = (5 * n + 1) % 16; }
        else if (n < 48) { F = B ^ C ^ D; g = (3 * n + 5) % 16; }
        else { F = C ^ (B | ~D); g = (7 * n) % 16; }
        F = (F + A + T[n] + m[g]) | 0;
        A = D; D = C; C = B;
        B = (B + ((F << S[n]) | (F >>> (32 - S[n])))) | 0;
      }
      a0 = (a0 + A) | 0; b0 = (b0 + B) | 0; c0 = (c0 + C) | 0; d0 = (d0 + D) | 0;
    }
    return hex([a0, b0, c0, d0], true);
  }

  var api = { sha256: sha256, md5: md5 };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Hash = api;
})(this);

import qrImage from 'qr-image';
import http from './http.js';

// TODO docs on how to use as image
const getQRDataURI = (data) => {
  let pngBuffer = qrImage.imageSync(data, {type: 'png'});
  return 'data:image/png;charset=utf-8;base64, ' + pngBuffer.toString('base64');
};

function updateQRCode() {
  let qrimage = document.getElementById('qrcode');
  let datael = document.getElementById('data');
  let array = new Uint8Array(8);
  window.crypto.getRandomValues(array);
  let token = '';
  for (var i = 0; i < array.length; i++) {
    let h = array[i].toString(16);
    if (h.length == 1) {
      token += '0' + h;
    } else {
      token += h;
    }
  }
  let url = document.location.protocol + '//' + document.location.hostname;
  if (document.location.protocol == 'http:') {
    if (document.location.port !== 80) {
      url += ':' + document.location.port;
    }
  } else if (document.location.protocol == 'https:') {
    // ... should never be a different port
  }
  url += '/admin/login/' + token;
  qrimage.src = getQRDataURI("web-signin:" + url);
  return token;
}

function run() {
  let token = updateQRCode();
  http('/admin/login/' + token).then((data) => {
    document.location.href = '/admin';
  }).catch(function(error) {
    console.log(error);
    run();
  });
}

run();

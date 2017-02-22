import http from './http.js';

http('/currentuser').then((data) => {
  let user = data['user'];
  let address = user['owner_address'];
  if (address) {
    let qrimage = document.getElementById('qrcode');
    let datael = document.getElementById('welcome-msg');
    qrimage.src = 'https://token-id-service.herokuapp.com/identicon/' + address + '.png';
    let msg1 = document.createElement('div');
    let msg2 = document.createElement('div');
    msg1.appendChild(document.createTextNode('Hello ' + user['username'] + '!!'));
    msg2.appendChild(document.createTextNode('Address: ' + address));
    datael.appendChild(msg1);
    datael.appendChild(msg2);
  }

  loadApps();

}).catch(function(error) {
  console.log(error);
});

function createRequestFeaturedButton(ftd, otd, address) {
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/registry/featured/add', {method: 'POST', data: {address: address}}).then((data) => {
      a.remove();
      ftd.appendChild(document.createTextNode("requested"));
      createRemoveFromFeaturedButton(ftd, otd, address);
    });
  }, false);
  a.appendChild(document.createTextNode("(request add to featured)"));
  otd.appendChild(a);
}

function createRemoveFromFeaturedButton(ftd, otd, address) {
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/registry/featured/remove', {method: 'POST', data: {address: address}}).then((data) => {
      a.remove();
      var item = ftd.childNodes[0];
      if (item) {
        item.remove();
      }
      createRequestFeaturedButton(ftd, otd, address);
    });
  }, false);
  a.appendChild(document.createTextNode("(remove from featured)"));
  otd.appendChild(a);
}

let apptable = document.getElementById('apps');
function newAppRow(app) {
  let newtr = document.createElement('tr');

  // icon
  let td_icon = document.createElement('td');
  let img_icon = document.createElement('img');
  img_icon.classList.add('appicon');
  img_icon.src = app['avatarUrl'];
  td_icon.appendChild(img_icon);

  let td_name = document.createElement('td');
  td_name.appendChild(document.createTextNode(app['displayName']));

  let td_featured = document.createElement('td');
  let td_featured_opts = document.createElement('td');
  if (app['featured']) {
    td_featured.appendChild(document.createTextNode("featured"));
  } else if (app['requestForFeatured']) {
    td_featured.appendChild(document.createTextNode("requested"));
  }
  if (app['featured'] || app['requestForFeatured']) {
    createRemoveFromFeaturedButton(td_featured, td_featured_opts, app['ownerAddress']);
  } else {
    createRequestFeaturedButton(td_featured, td_featured_opts, app['ownerAddress']);
  }

  newtr.appendChild(td_icon);
  newtr.appendChild(td_name);
  newtr.appendChild(td_featured);
  newtr.appendChild(td_featured_opts);

  apptable.appendChild(newtr);
  if (apptable.children.length % 2 == 0) {
    newtr.classList.add('oddrow');
  }
}

function loadApps() {
  http('/registry/apps').then((data) => {
    let apps = data['apps'];
    for (var i = 0; i < apps.length; i++) {
      let app = apps[i];
      newAppRow(app);
    }
  });
}

let form = document.getElementById('newappform');
form.addEventListener('submit', (event) => {
  event.preventDefault();
  let elems = document.forms['newappform'].elements;
  let avatar_url = elems['avatar_url'].value;
  let owner_address = elems['owner_address'].value;
  let display_name = elems['display_name'].value;
  http('/registry/apps', {
    method: 'POST',
    data: {
      'avatar_url': avatar_url,
      'owner_address': owner_address,
      'display_name': display_name
    }
  }).then((data) => {
    newAppRow(data);
  });
});

import http from './http.js';

http('/currentuser').then((data) => {
  let user = data['user'];
  let address = user['token_id'];
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

function removeChildren(el) {
  if (el.childNodes) {
    while (el.childNodes.length > 0) {
      el.childNodes[0].remove();
    }
  }
}

let apptable = document.getElementById('apps-table');
function newAppRow(app, tr) {
  let newtr = tr || document.createElement('tr');

  let td_icon = document.createElement('td');
  let td_name = document.createElement('td');

  function add_icon_and_name() {
    // config icon
    let img_icon = document.createElement('img');
    img_icon.classList.add('appicon');
    img_icon.src = app['avatarUrl'];
    td_icon.appendChild(img_icon);

    // name
    td_name.appendChild(document.createTextNode(app['displayName']));
  }

  // address
  let td_address = document.createElement('td');
  td_address.appendChild(document.createTextNode(app['ownerAddress']));

  // featured
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

  let td_opts = document.createElement('td');

  function editme() {
    removeChildren(td_icon);
    removeChildren(td_name);
    removeChildren(td_opts);

    let editicon = document.createElement('input');
    editicon.value = app['avatarUrl'];
    td_icon.appendChild(editicon);
    let editname = document.createElement('input');
    editname.value = app['displayName'];
    td_name.appendChild(editname);
    let savea = document.createElement('a');
    savea.href = '';
    savea.addEventListener('click', (event) => {
      event.preventDefault();
      removeChildren(td_icon);
      removeChildren(td_name);
      removeChildren(td_opts);
      app['avatarUrl'] = editicon.value;
      app['displayName'] = editname.value;
      add_icon_and_name();
      addeditlink();
      http('/registry/apps', {
        method: 'PUT',
        data: {
          'avatar_url': editicon.value,
          'token_id': app['ownerAddress'],
          'display_name': editname.value
        }
      });
    }, false);
    savea.appendChild(document.createTextNode("(save)"));
    let cancelsavea = document.createElement('a');
    cancelsavea.href = '';
    cancelsavea.addEventListener('click', (event) => {
      event.preventDefault();
      removeChildren(td_icon);
      removeChildren(td_name);
      removeChildren(td_opts);
      add_icon_and_name();
      addeditlink();
    }, false);
    cancelsavea.appendChild(document.createTextNode("(cancel)"));
    td_opts.appendChild(savea);
    td_opts.appendChild(cancelsavea);
  }

  function addeditlink() {
    let edita = document.createElement('a');
    edita.href = '';
    edita.addEventListener('click', (event) => {
      event.preventDefault();
      editme();
    }, false);
    edita.appendChild(document.createTextNode("(edit)"));
    td_opts.appendChild(edita);
  }

  newtr.appendChild(td_icon);
  newtr.appendChild(td_name);
  newtr.appendChild(td_address);
  newtr.appendChild(td_featured);
  newtr.appendChild(td_featured_opts);
  newtr.appendChild(td_opts);
  add_icon_and_name();
  addeditlink();

  if (!tr) {
    apptable.appendChild(newtr);
    if (apptable.children.length % 2 == 0) {
      newtr.classList.add('oddrow');
    }
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
  let token_id = elems['token_id'].value;
  let display_name = elems['display_name'].value;
  http('/registry/apps', {
    method: 'POST',
    data: {
      'avatar_url': avatar_url,
      'token_id': token_id,
      'display_name': display_name
    }
  }).then((data) => {
    newAppRow(data);
  });
});

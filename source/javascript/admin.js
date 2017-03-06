import http from './http.js';

const id_service_url = process.env.ID_SERVICE_URL;

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
  loadAdmins();
  document.getElementsByTagName("BODY")[0].classList.remove('hidden');

}).catch(function(error) {
  console.log(error);
});

// APPS setup

function createAddToFeaturedButton(ftd, otd, address) {
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/admin/featured/add', {method: 'POST', data: {address: address}}).then((data) => {
      a.remove();
      var item = ftd.childNodes[0];
      if (item) {
        item.remove();
      }
      item = otd.childNodes[0];
      if (item) {
        item.remove();
      }
      ftd.appendChild(document.createTextNode("featured"));
      createRemoveFromFeaturedButton(ftd, otd, address);
    });
  }, false);
  a.appendChild(document.createTextNode("(add)"));
  otd.appendChild(a);
}

function createRemoveFromFeaturedButton(ftd, otd, address) {
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/admin/featured/remove', {method: 'POST', data: {address: address}}).then((data) => {
      a.remove();
      var item = ftd.childNodes[0];
      if (item) {
        item.remove();
      }
      createAddToFeaturedButton(ftd, otd, address);
    });
  }, false);
  a.appendChild(document.createTextNode("(remove)"));
  otd.appendChild(a);
}

function createRejectFeaturedButton(ftd, otd, address) {
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/admin/featured/reject', {method: 'POST', data: {address: address}}).then((data) => {
      a.remove();
      var item = ftd.childNodes[0];
      if (item) {
        item.remove();
      }
    });
  }, false);
  a.appendChild(document.createTextNode("(reject)"));
  otd.appendChild(a);
}

let apptable = document.getElementById('apps-table');
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
    createRemoveFromFeaturedButton(td_featured, td_featured_opts, app['ownerAddress']);
  } else {
    if (app['requestForFeatured']) {
      td_featured.appendChild(document.createTextNode("requested"));
      createRejectFeaturedButton(td_featured, td_featured_opts, app['ownerAddress']);
    }
    createAddToFeaturedButton(td_featured, td_featured_opts, app['ownerAddress']);
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
  http('/admin/apps').then((data) => {
    let apps = data['apps'];
    for (var i = 0; i < apps.length; i++) {
      let app = apps[i];
      newAppRow(app);
    }
  });
}

// ADMINS SETUP

let admintable = document.getElementById('admins-table');
function newAdminRow(admin) {
  let newtr = document.createElement('tr');

  // icon
  let td_icon = document.createElement('td');
  let img_icon = document.createElement('img');
  img_icon.classList.add('appicon');
  let avatar = admin['custom']['avatar'];
  if (!avatar) {
    avatar = '/identicon/' + admin['token_id'] + '.png';
  }
  if (avatar.substring(0, 11) == '/identicon/') {
    avatar = id_service_url + avatar;
  }
  img_icon.src = avatar;
  td_icon.appendChild(img_icon);

  let td_name = document.createElement('td');
  td_name.appendChild(document.createTextNode(admin['username']));

  let td_address = document.createElement('td');
  td_address.appendChild(document.createTextNode(admin['token_id']));

  let td_opts = document.createElement('td');
  let a = document.createElement('a');
  a.href = '';
  a.addEventListener('click', (event) => {
    event.preventDefault();
    http('/admin/admins/remove', {method: 'POST', data: {address: admin['token_id']}}).then((data) => {
      newtr.remove();
    });
  }, false);
  a.appendChild(document.createTextNode("(remove)"));
  td_opts.appendChild(a);

  newtr.appendChild(td_icon);
  newtr.appendChild(td_name);
  newtr.appendChild(td_address);
  newtr.appendChild(td_opts);

  admintable.appendChild(newtr);
  if (admintable.children.length % 2 == 0) {
    newtr.classList.add('oddrow');
  }
}

let searchinput = document.getElementById("admins-search-input");
let searchingindicator = document.getElementById('admins-searching-indicator');
let searchresults = document.getElementById("admins-search-results");
let latestsearchfuture = null;
function clearSearchResults() {
  while (searchresults.childNodes.length > 0) {
    searchresults.childNodes[0].remove();
  }
}
function addSearchResult(user) {
  let li = document.createElement("LI");
  li.appendChild(document.createTextNode(user['username'] + " (" + user['token_id'] + ")"));
  li.addEventListener('click', (event) => {
    http('/admin/admins/add', {method: 'POST', data: {address: user['token_id']}}).then((data) => {
      newAdminRow(user);
      searchinput.value = '';
      clearSearchResults();
    });
  });
  searchresults.appendChild(li);
}
function searchAdmins() {
  if (searchinput.value == '') {
    searchingindicator.classList.add('hidden');
    clearSearchResults();
  } else {
    searchingindicator.classList.remove('hidden');
    let fut = latestsearchfuture = http('/admin/admins/search?query=' + searchinput.value).then((data) => {
      if (fut === latestsearchfuture) {
        clearSearchResults();
        searchingindicator.classList.add('hidden');
        for (var i = 0; i < data.results.length; i++) {
          var user = data.results[i];
          addSearchResult(user);
        }
      }
    });
  }
}
let searchtimeout = null;
searchinput.addEventListener('keyup', (event) => {
  clearTimeout(searchtimeout);
  searchtimeout = setTimeout(() => { searchAdmins(); }, 500);
});

function loadAdmins() {
  http('/admin/admins').then((data) => {
    let admins = data['admins'];
    for (var i = 0; i < admins.length; i++) {
      let app = admins[i];
      newAdminRow(app);
    }
  });
}


// NAV SETUP

let nav = document.getElementById("nav");
function setActiveNav(id) {
  for (var i = 0; i < nav.childNodes.length; i++) {
    let node = nav.childNodes[i];
    if (node.nodeType == 3) {
      continue;
    }
    if (node.id == id) {
      node.classList.add('active');
    } else {
      node.classList.remove('active');
    }
  }
}

let pages = document.getElementById("pages");
function setActivePage(id) {
  for (var i = 0; i < pages.childNodes.length; i++) {
    let node = pages.childNodes[i];
    if (node.nodeType == 3) {
      continue;
    }
    if (node.id == id) {
      node.classList.remove('hidden');
    } else {
      node.classList.add('hidden');
    }
  }
}
let appsnav = document.getElementById("appsnav");
appsnav.addEventListener('click', (event) => {
  setActiveNav('appsnav');
  setActivePage('apps-page');
});
let adminsnav = document.getElementById("adminsnav");
adminsnav.addEventListener('click', (event) => {
  setActiveNav('adminsnav');
  setActivePage('admins-page');
});

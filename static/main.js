let at_bottom = false;
var skeds = {};
var spots = {};

/*
* convert the a JSON spot object into HTML
* 
* param: spot - json object returned from flask app
* returns: string with html representation of the spot param
*/
function getSpotHtml(spot) {
    var out = '';
    var spot_class = "spotline";
    if (spot.flag) {
        spot_class += " newhighlight";
    }

    out += '<div class="' + spot_class + '">';
    out += '<span class="zulu">' + spot.time + '</span>' +
        '<span class="callsign"> ' + spot.call + ' </span>' +
        '<span class="freq">' + spot.freq + '</span>' +
        '<span class="spotter"> ' + spot.spotter + ' </span>' +
        '<span class="skcc_info"> (' + spot.num + ' ' + spot.name + ' ' + spot.spc + ') </span>' +
        '';
    out += '<span class="youneed fw-lighter"> ' + spot.you_need + '</span>';
    if (spot.they_need !== "") {
        out += '<span class="theyneed fw-lighter"> / they: ' + spot.they_need + '</span>';
    }
    out += '<span class="sked_status"> ' + spot.sked_stat + '</span>';
    out += "<br>";
    out += '</div>';
    return out;
}

/* 
*  Write out the HTML for a the spot array (arr) to the 
*  element at (id).
*/
function writeSpotLines(arr, id) {
    var out = '';
    var i;
    for (i = 0; i < arr.length; i++) {

        out += getSpotHtml(arr[i]);
    }
    document.getElementById(id).innerHTML = out;

    /* scroll to bottom of spot div if its already at the bottom (tail -f behavior) */
    if (id == "spots" && at_bottom) {
        scrollToBottom(id);
    }
}

/*
* Scroll to the bottom of an overflow div with given ID
*/
function scrollToBottom(id) {
    var div = document.getElementById(id);
    var scrollHeight = Math.max(div.scrollHeight, div.clientHeight);
    div.scrollTop = scrollHeight - div.clientHeight;
}

/*
* Write the skimmer status data to the status div.
*
* param: jsonData: an array of text lines in a json array.
*/
function writeStatus(jsonData) {
    var i = 0;
    var out = '<pre>';

    for (i = 1; i < jsonData.length; i++) {
        out += '<div class="statusline">';
        out += jsonData[i];
        out += '</div>';
    }
    out += '</pre>';

    document.getElementById('status').innerHTML = out;
}

/* 
* SPOTS WEBSOCKET 
*/
const spotsWebsocket = new WebSocket('ws://' + location.host + '/getspotsws');
spotsWebsocket.addEventListener('message', ev => {
    jsonData = JSON.parse(ev.data);
    writeSpotLines(jsonData, "spots");
    spots = jsonData;
});

/* 
* SKEDS WEBSOCKET 
*/
const skedsWebsocket = new WebSocket('ws://' + location.host + '/getskedsws');
skedsWebsocket.addEventListener('message', ev => {
    jsonData = JSON.parse(ev.data);
    writeSpotLines(jsonData, "skeds");
    skeds = jsonData;
});

function get_status() {
    // create an ajax request
    var q = new XMLHttpRequest();
    q.open("get", '/getstatus', true);
    q.send();

    q.onload = function () {
        var v = JSON.parse(q.responseText);

        writeStatus(v);

        // v[0] is the current cSkimmer state value. either starting
        // or running
        if (v[0] != "running")
            setTimeout(get_status, 1000);
    };
};

get_status(); // call the function to get it started

function updateClock() {
    var t = new Date().toUTCString();
    document.getElementById('time').innerHTML = t;

    // call this function again in 1000ms
    setTimeout(updateClock, 1000);
};

updateClock(); // call the function to get it started


function save_spot() {
    var q = new XMLHttpRequest();
    q.open("post", '/save/', true);
    q.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    q.send(JSON.stringify(f));
};

var q = new XMLHttpRequest();
q.open("get", '/load', true);
q.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
q.send();
q.onload = function () {
    var v = JSON.parse(q.responseText);
    v.forEach(el => $('#scratchpad').append(getSpotHtml(el)));
    /*$('#scratchpad').append(getSpotHtml(v[0]));*/
};


/* toggle the Highlight on a spotline on click */
$(document).on("click", 'div.spotline', function (event) {
    if ($(this).hasClass("highlight"))
        $(this).removeClass("highlight");
    else {
        $(this).addClass("highlight");

        /* add to the scratch pad div */
        let savedLine = $(this).clone();
        $('#scratchpad').append(savedLine);

        let cs = $(this).find('.callsign');
        let toFind = cs[0].innerHTML.trim();

        if ($(event.target).parents("#spots").length > 0) {
            var f = spots.find(el => el.call === toFind);
        }
        else {
            var f = skeds.find(el => el.call === toFind);
        }
        console.log(f);

        var q = new XMLHttpRequest();
        q.open("post", '/save/', true);
        q.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        q.send(JSON.stringify(f));
    }
});

/* Detect if the user has scrolled to bottom of SPOTS div */
$('#spots').on('scroll', function () {
    var x = this.scrollHeight - Math.round(this.scrollTop);

    if (x === this.clientHeight) {
        at_bottom = true;
    }
    else {
        /* user scrolled back up. this flag is now set so the
        spot list doesn't auto jump to bottom of div */
        at_bottom = false;
    }

});


/*
* clear the scratch pad div and clear the session data via http post
*/
function onScratchPadClearClick() {
    $('#scratchpad').empty();

    var q = new XMLHttpRequest();
    q.open("post", '/save/?clear=1', true);
    q.send();
}


/*
*  Play button click handler. 
*/
function onPlayClick() {
    scrollToBottom("spots");
}


/*
 * Restart button click handler
 */
function onRestartClick() {
    var q = new XMLHttpRequest();
    q.open("post", '/restart/', true);
    q.send();

    /* when post is done */
    q.onreadystatechange = () => {
        if (q.readyState === XMLHttpRequest.DONE) {
            const status = q.status;
            if (status === 0 || (status >= 200 && status < 400)) {
                /* kick off the status check ajax */
                get_status();
            }
        }
    };


}
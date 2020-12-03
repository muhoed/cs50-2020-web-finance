function negativeNumbers() {
    var money = document.getElementsByClassName("shares");
    for (var i = 0, len = money.length; i < len; i++) {
      if (money[i].innerHTML < 0 || money[i].innerHTML.indexOf("-") > -1) {
          money[i].style.color = "red";
      }
    }
}

function calcTrans(avgprice, price, shares){
    proceeds = shares * price;
    pl = shares * price - shares * avgprice;
    document.getElementById("proceeds").innerHTML = proceeds.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
    document.getElementById("pl").innerHTML = pl.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
    negativeNumbers();
}

function calcCash(price, shares){
    required = price * shares;
    document.getElementById("required").innerHTML = required.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
    negativeNumbers();
}

function formatCurr () {
    var cur = document.getElementsByClassName("currency");
    for (var i = 0, len = cur.length; i < len; i++) {
        var num = Number(cur[i].innerHTML)
        cur[i].innerHTML = num.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
    }
}

function sortTable(sortBy, sortOrder, tableType) {
    var xhttp;
    var filterBy;
    if (sortBy == "") {
        sortBy = document.getElementById("sort").value;
    }
    if (sortOrder == "") {
        sortOrder = document.getElementById("order").value;
    }
    var filterCheck = document.getElementById("filterBy");
    if (filterCheck) {
        if (filterCheck.value != "" && filterCheck.value != "all") {
            filterBy = filterCheck.value;
        } else {
            filterBy = "all";
        }
    } else {
        filterBy = "all"
    }
    if (tableType == "") {
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("sorted").innerHTML = this.responseText;
            negativeNumbers();
            formatCurr();
        }
    };
    xhttp.open("POST", $SCRIPT_ROOT + "/_sort_table", true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.send("sortBy=" + sortBy + "&sortOrder=" + sortOrder + "&tableType=" + tableType + "&filterBy=" + filterBy);
}



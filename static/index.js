function delete_staff(staff_id) {
    var deleting_id = document.getElementById('delete_staff');
    staff_id = deleting_id.value
    fetch("/delete-staff", {
        method: "POST",
        body: JSON.stringify({ staff_id: staff_id }),
    }).then((_res) => {
        window.location.href = "/staff";
    });
}

function type_selection() {
    var type_selected = document.getElementById('type');
    let mbike;
    if (type_selected == 'Motorbike') {
        mbike = true;
    }
    fetch("/vehicle_reg", {
        method: "POST",
        body: JSON.stringify(mbike)
    })
}

// function select_parts(p1, p2) {
//     var p1 = document.getElementById(p1);
//     var p2 = document.getElementById(p2);
//     p2.innerHTML = ""

//     options = "{% for part in parts['" + p1.value + "'] %} <option value={{part}}>{{part}}</option> {% endfor %}"
//     p2.innerHTML = options
// }

//function to dynamically change cars' parts in a dropdown menu. Got it on https://www.youtube.com/watch?v=I2dJuNwlIH0
function set_list() {
    let p1 = document.getElementById('part1');
    let p2 = document.getElementById('part2');

    system_selected = p1.value;

    fetch('parts/' + system_selected).then(function (response) {
        response.json().then(function (data) {
            let optionHTML = '';

            for (individual_parts in data) {
                individual_parts.replace(" ", "&nbsp")
                optionHTML += '<option value="' + individual_parts + '">' + individual_parts + "</option>";
            }

            p2.innerHTML = optionHTML;
        })
    })
    p2.innerHTML = ""

    options = "{% for part in parts['" + p1.value + "'] %} <option value={{part}}>{{part}}</option> {% endfor %}"
    p2.innerHTML = options


};

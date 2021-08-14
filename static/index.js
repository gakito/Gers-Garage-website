//getting the staff data from the database and sending it to the backend to delete it from the database
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

//jQuery to generate a Datepicker when making a booking
$(document).ready(function () {
    $(function () {
        //setting date format and the range of possible days
        $("#date").datepicker({
            dateFormat: 'dd-mm-yy',
            maxDate: '+60d',
            minDate: '+1d',
            disableEntry: true,

            //Block sundays 
            beforeShowDay: function (date) {
                var day = date.getDay();
                return [(day != 0), ''];
            }
        });
    });
})

//automatically closes the messages shown to users
setTimeout(function () {
    $('.alert').fadeOut('fast');
}, 4000);
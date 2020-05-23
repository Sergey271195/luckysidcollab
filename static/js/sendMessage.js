window.onload = () => (

checkLocalStorage(),
$('#stop_update_btn').hide(),
$('#message_input').val('')

)

let updateInterval

$('#send_message_btn').on('click', () => {
    sendMessage()
})

$('#message_input').keypress((e) => {
    if (e.which == 13) {
        sendMessage()
        return false;
    }
})

$('#stop_update_btn').on('click', () => {
    $('#stop_update_btn').hide()
    clearInterval(updateInterval)
    $('#update_btn').show()
})

$('#update_btn').on('click', () => {
    $('#update_btn').hide()
    $('#stop_update_btn').show()
    updateInterval = setInterval(timedUpdate, 10000)
})

$('#user_id').on('change', function() {
    localStorage.setItem('user_id', this.value),
    $.ajax({
        url: '/telegram',
        type: 'get',
        data: {user_id: this.value},
        success: data => updateView(data)
    })
  });

checkLocalStorage = () => {
    if (localStorage.getItem('user_id') !== null) {
        let user_id = localStorage.getItem('user_id')
        $(`#user_id option[value="${user_id}"]`).attr('selected', 'selected')
        timedUpdate()
    }

    else {
        let user_id = $('#user_id').find(":selected").text();
        localStorage.setItem('user_id', user_id)
    }
}

updateView = (data) => {

    let update_messages = data.update
    let resulting_div = $('#user_messages')

    $('#username').empty()
    $('#username').append(data.username)

    $(resulting_div).empty()

    update_messages.forEach((element, index) => {
        let first_div = `<div><span class = 'font-weight-bold'>Date</span>: ${element.message.date}</div>`
        let second_div = `<div><span class = 'font-weight-bold'>Message</span>: ${element.message.text}</div>`
        let container = `<div class = 'container mb-3'>
                            ${first_div}
                            ${second_div}
                        </div>`
        $(resulting_div).append(container)
    });

}

timedUpdate = () => {
    console.log('Updating ...')
    let user_id = localStorage.getItem('user_id')
    $.ajax({
        url: '/telegram',
        type: 'get',
        data: {user_id: user_id},
        success: data => updateView(data)
    })
}

sendMessage = () => {
    let message = $('#message_input').val()
    $('#message_input').val('')
    $.ajax({
        url: '/telegram',
        type: 'get',
        data: {user_id: localStorage.getItem('user_id'), message: message},
        success: () => timedUpdate()
    })
}
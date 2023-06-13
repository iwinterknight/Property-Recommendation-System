//add img link
// const imglink = "";
class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            displayImage: document.querySelector('.slide-image'),
            initiateDialogButton: document.querySelector('.initiatedialog__button')
        }

        this.state = false;
        this.messages = [];
    }

    display() {
        const {openButton, chatBox, sendButton, displayImage} = this.args;

        var html = `<img src="https://imageio.forbes.com/specials-images/imageserve/5f5e4bd9f5e52c52acbcd758/The-Oval-campus-lawn-park-Ohio/960x0.jpg?format=jpg&width=960" width="1200" height="1000" alt="image">`
        displayImage.innerHTML = html

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox, displayImage))

        initiateDialogButton.addEventListener('click', () => this.initiateDialog())

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key === "Enter") {
                this.onSendButton(chatBox, displayImage)
            }
        })
    }

    initiateDialog(chatbox, displayimage) {
        var textField = chatbox.querySelector('input');
        fetch($SCRIPT_ROOT + '/initiate_dialog', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {
            textField.value = ''
            var html = `<img src="https://imageio.forbes.com/specials-images/imageserve/5f5e4bd9f5e52c52acbcd758/The-Oval-campus-lawn-park-Ohio/960x0.jpg?format=jpg&width=960" width="1200" height="1000" alt="image">`
            displayImage.innerHTML = html

        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
          });
    }

    toggleState(chatbox) {
        this.state = !this.state;

        // show or hides the box
        if(this.state) {
            chatbox.classList.add('chatbox--active')
        } else {
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox, displayimage) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === "") {
            return;
        }

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);
        this.updateChatText(chatbox);
        textField.value = '';

        fetch($SCRIPT_ROOT + '/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {
            let msg2 = { name: "Agent", message: r.answer, image: r.image_url };
            this.messages.push(msg2);
            this.updateChatText(chatbox)

            if (r.image_url !== '')
            {
                this.updateImage(displayimage)
            }

            textField.value = ''

        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
          });
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach(function(item, index) {
            if (item.name === "Chatbot")
            {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
            }
            else
            {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
            }
          });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }

    updateImage(displayimage) {
        var html = '';

        if (this.messages[this.messages['length']-1].name === "Chatbot")
        {
            html = `<img src=` + this.messages[this.messages['length']-1].image + ` width="1200" height="1000" alt="image">`
        }

        displayimage.innerHTML = html
    }
}


const chatbox = new Chatbox();
chatbox.display();

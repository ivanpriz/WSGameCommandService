let clientId = null;
let playerColor = null;

let ws = new WebSocket("ws://localhost:7000/ws")
const divPlayers = document.getElementById("divPlayers");
const divBoard = document.getElementById("divBoard");


function movePlayerToCell(event) {
    let el = event.currentTarget
    ws.send(
        JSON.stringify(
            {
                "method": "MOVE",
                "payload": [
                    el.getAttribute("data-x"),
                    el.getAttribute("data-y"),
                ]
            }
        )
    )
}

ws.onmessage = message => {
    const response = JSON.parse(message.data);

    if (!response.success) { return }

    if (response.method == "UPDATE_BOARD") {
        for(let y=0; y<response.payload.board.length; y++) {
            for(let x=0; x<response.payload.board[y].length; x++) {
                const color = response.payload.board[y][x];
                const cellObject = document.querySelector(`.cell[data-x='${x}'][data-y='${y}']`);
                cellObject.style.backgroundColor = color
            }
        }
    } else if (response.method == "MSG") {
            let li = document.createElement("li")
            li.appendChild(document.createTextNode(response.text))
            document.getElementById("log").appendChild(li)
    }
};
const cells = document.querySelectorAll(".cell");
cells.forEach((cell) => {cell.addEventListener("click", movePlayerToCell)});
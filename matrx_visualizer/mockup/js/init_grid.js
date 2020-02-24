var rows = 10;
var columns = 10;
var agents = ["agent_1", "agent_2"];
var agent_locations = [[1, 1], [3, 3]];
var grid = document.getElementById("grid");

for (var x = 0; x < columns; x++) {
  var row = document.createElement("div");
  row.className = "row";
  grid.appendChild(row);

  for (var y = 0; y < rows; y++) {  // Check if there is an agent in this location
    loc = [x, y];
    var agent_id = null;
    var i = 0;
    while (i < agent_locations.length) {
      if (equals(loc, agent_locations[i])) {
        agent_id = "agent_" + loc.toString();
        break;
      } else {
        i++;
      }
    }
    if (agent_id != null) { // If there's an agent in this location, add it
      var agent = document.createElement("div");
      agent.className = "agent";
      agent.id = agent_id;
      agent.dataset.toggle = "modal";
      agent.dataset.target = "#agent_modal";
      agent.onclick = "clickAgent(id)"; // TODO fix this
      agent.innerHTML = agent_id;
      row.append(agent);

    } else {  // Else add an empty cell
      var cell = document.createElement("div");
      cell.className = "cell";
      id = x.toString() + "_" + y.toString();
      cell.id = "cell_" + id;
      cell.onclick = "drawCell(id)";  // TODO fix this
      row.append(cell);
    }
  }
}

function equals(array1, array2) {
  return array1.length === array2.length && array1.every(function(value, index) { return value === array2[index]})
}

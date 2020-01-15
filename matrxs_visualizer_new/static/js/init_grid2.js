var grid_size = [10, 10];
var agents = ["agent_1", "agent_2"];
var agent_locations = [[1, 1], [3, 3]];

var cell_size = calcCellSize(grid_size);
var grid = document.getElementById("grid");

// Add cells to grid
for (var x = 0; x < grid_size[0]; x++) {
  for (var y = 0; y < grid_size[1]; y++) {
    var cell = document.createElement("div");
    cell.className = "cell";
    cell.id = "cell_" + x.toString() + "_" + y.toString();
    cell.onclick = "drawCell(id)";  // TODO fix this
    var pos_x = x * cell_size;
    var pos_y = y * cell_size;
    cell.style = "position:absolute; left:" + pos_x + "em; top:" + pos_y + "em;";
    grid.append(cell);
  }
}

// Add agents to grid
for (var i = 0; i < agents.length; i++) {
  agent_id = agents[i];
  var agent = document.createElement("div");
  agent.className = "agent";
  agent.id = agent_id;
  agent.dataset.toggle = "modal";
  agent.dataset.target = "#agent_modal";
  agent.onclick = "clickAgent(id)"; // TODO fix this
  agent.innerHTML = agent_id;
  var pos_x = agent_locations[i][0] * cell_size;
  var pos_y = agent_locations[i][1] * cell_size;
  agent.style = "position:absolute; left:" + pos_x + "em; top:" + pos_y + "em;";
  grid.append(agent);
}

// TODO function that calculates cell size based on size of the grid
function calcCellSize(grid_size) {
    var cell_size = 5;
    return cell_size
}

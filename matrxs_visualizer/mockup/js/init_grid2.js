var grid_size = [10, 10];
var agents = ["agent_1", "agent_2", "agent_3"];
var agent_locations = [[1, 1], [3, 3], [9, 9]];

var cell_size = calcCellSize(grid_size);
var grid = document.getElementById("grid");

// Add cells to grid
for (var x = 0; x < grid_size[0]; x++) {
  for (var y = 0; y < grid_size[1]; y++) {
    var cell = document.createElement("div");
    cell.className = "cell";
    cell.id = "cell_" + x.toString() + "_" + y.toString();
    cell.setAttribute("onmousedown", "startDrawErase(id)");
    cell.setAttribute("onmouseup", "stopDrag()");
    var pos_x = x * cell_size;
    var pos_y = y * cell_size;
    cell.style = "position:absolute; left:" + pos_x + "em; top:" + pos_y + "em; height:" + cell_size + "em; width:" + cell_size + "em;";
    grid.append(cell);
  }
}

// Add agents to grid
for (var i = 0; i < agents.length; i++) {
  // Div that combines agent with its menu
  var dropdown = document.createElement("div");
  grid.append(dropdown);

  // Agent object
  agent_id = agents[i];
  var agent = document.createElement("div");
  agent.className = "agent";
  agent.id = agent_id;
  agent.dataset.toggle = "dropdown";
  agent.innerHTML = agent_id;
  var pos_x = agent_locations[i][0] * cell_size;
  var pos_y = agent_locations[i][1] * cell_size;
  agent.style = "position:absolute; left:" + pos_x + "em; top:" + pos_y + "em; height:" + cell_size + "em; width:" + cell_size + "em;";
  dropdown.append(agent);

  // Menu
  var agent_menu = document.createElement("div");
  agent_menu.className = "dropdown-menu";
  agent_menu.id = agent_id;

  // Menu items
  var menu_item = document.createElement("a");
  menu_item.className = "dropdown-item";
  menu_item.id = agent_id;
  menu_item.href = "";
  menu_item.setAttribute("onclick", "agentAction(id)");
  menu_item.innerHTML = "Action 1"
  agent_menu.append(menu_item);
  agent.append(agent_menu);

  var menu_item2 = document.createElement("a");
  menu_item2.className = "dropdown-item";
  menu_item2.id = agent_id;
  menu_item2.href = "";
  menu_item2.setAttribute("onclick", "agentAction(id)");
  menu_item2.innerHTML = "Action 2"
  agent_menu.append(menu_item2);
  agent.append(agent_menu);
}

// TODO function that calculates cell size based on size of the grid
function calcCellSize(grid_size) {
    var cell_size = 5;
    return cell_size
}

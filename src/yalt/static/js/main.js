document.getElementById("get-sample").addEventListener(
  "click", ()=>{eel.get_sample()}, false
);
document.getElementById("print-sample").addEventListener(
  "click", ()=>{alert(sample["text"])}, false
);

sample = {}
eel.expose(set_sample);
function set_sample(json_str) {
  sample = json_str
}

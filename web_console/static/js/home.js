function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function onload() {
    update_state()
    setInterval(update_state, 3000);
}

async function update_state() {
    if (document.hidden) {
        return;
    }
    function net_retouch(inp, target) {
        let table = ["KB", "MB", "GB"];
        let table_num = 0;
        inp /= 1024;
        target /= 1024
        while (target >= 1000) {
            inp /= 1024;
            target /= 1024
            table_num += 1;
        }
        return inp.toFixed(1).toString() + " " + table[table_num] + "/s"
    };
    function get_val(ele) {
        return parseFloat(getComputedStyle(ele.getElementsByTagName("circle")[1]).getPropertyValue("--percent"))
    }
    let response = await fetch(document.location.origin + "/api/v1.0/system_state");
    let data = JSON.parse(await response.text());
    let target = {
        "cpu": data.cpu_percent,
        "ram": data.ram_percent,
        "upload": data.upload_speed,
        "download": data.download_speed
    };
    let cpu_ele = document.getElementById("cpu");
    let ram_ele = document.getElementById("ram");
    let upload_ele = document.getElementById("upload");
    let download_ele = document.getElementById("download");
    let offset = {
        "cpu": (target.cpu - get_val(cpu_ele)) / 200,
        "ram": (target.ram - get_val(ram_ele)) / 200,
        "upload": (target.upload - get_val(upload_ele)) / 200,
        "download": (target.download - get_val(download_ele)) / 200
    };
    for (let i = 0; i < 200; i++) {
        cpu_ele.getElementsByTagName("circle")[1].style.setProperty("--percent", get_val(cpu_ele) + offset.cpu);
        cpu_ele.getElementsByTagName("p")[0].textContent = parseInt(get_val(cpu_ele)).toString() + " %"
        ram_ele.getElementsByTagName("circle")[1].style.setProperty("--percent", get_val(ram_ele) + offset.ram);
        ram_ele.getElementsByTagName("p")[0].textContent = parseInt(get_val(ram_ele)).toString() + " %"

        upload_ele.getElementsByTagName("circle")[1].style.setProperty("--percent", get_val(upload_ele) + offset.upload);
        upload_ele.getElementsByTagName("p")[0].textContent = net_retouch(get_val(upload_ele), target.upload)
        download_ele.getElementsByTagName("circle")[1].style.setProperty("--percent", get_val(download_ele) + offset.download);
        download_ele.getElementsByTagName("p")[0].textContent = net_retouch(get_val(download_ele), target.download)
        await sleep(6);
    }
}
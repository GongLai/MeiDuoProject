var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        cart_total_count: 0, // 购物车总数量
        carts: [], // 购物车数据,
        hots: [],
        category_id: category_id,
        username: '',
    },
    mounted(){
        // 获取购物车数据
        this.get_carts();

        // 获取热销商品数据
        this.get_hot_goods();

        this.username = getCookie('username');
    },
    methods: {
        // 获取购物车数据
        get_carts(){
            var url = this.host + '/carts/simple/';
            axios.get(url, {
                responseType: 'json',
            })
                .then(response => {
                    this.carts = response.data.cart_skus;
                    this.cart_total_count = 0;
                    for (var i = 0; i < this.carts.length; i++) {
                        if (this.carts[i].name.length > 25) {
                            this.carts[i].name = this.carts[i].name.substring(0, 25) + '...';
                        }
                        this.cart_total_count += this.carts[i].count;
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 获取热销商品数据
        get_hot_goods(){
            var url = this.host + '/hot/' + this.category_id + '/';
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    this.hots = response.data.hot_skus;
                    for (var i = 0; i < this.hots.length; i++) {
                        this.hots[i].url = '/goods/' + this.hots[i].id + '.html';
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        }
    }
});
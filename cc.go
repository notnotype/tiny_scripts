package main

import (
	"fmt"
	"net"
	"net/http"
	purl "net/url"
	"os"
	"strconv"
	"time"
)

var debug = false

const RED = "\033[1;31m"
const GREEN = "\033[1;32m"
const YELLOW = "\033[1;33m"
const BLUE = "\033[1;34m"
const RESET = "\033[0m"

func CC(url string, num int, ch chan int) {
	c := &http.Client{
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout:   40 * time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   10 * time.Second,
			ResponseHeaderTimeout: 15 * time.Second,
			ExpectContinueTimeout: 5 * time.Second,
		},
	}

	for {
		r, err := c.Get(url)
		if err != nil {
			err2, _ := err.(*purl.Error)
			if err2.Timeout() {
				// fmt.Println("timeout")
			} else {
				ch <- 0
				fmt.Printf("%sRoutine %d: %s%s\n", RED, num, err2, RESET)
				if debug {
					fmt.Printf("%sRoutine %d: %s%s\n", RED, num, err2, RESET)
				}
			}
			continue
		}
		if r.StatusCode == 200 {
			if debug {
				fmt.Printf(GREEN+"[Routine %5d]当前CC状态:%d](๑•॒̀ ູ॒•́๑)啦啦啦\n"+RESET, num, r.StatusCode)
			}
		} else {
			if debug {
				fmt.Printf(GREEN+"[Routine %5d]当前CC状态:%4d](ﾉ｀⊿´)ﾉ\n"+RESET, num, r.StatusCode)
			}
		}
		ch <- r.StatusCode
		err = r.Body.Close()
		if err != nil {
			ch <- 0
			continue
		}
	}
}

func main() {

	var ch = make(chan int)
	if len(os.Args) < 3 {
		fmt.Println("Usage: cc [-d] <url> <routine_num>")
		return
	}

	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-d" {
			fmt.Printf(RED + "Debug mode enabled\n" + RESET)
			debug = true
		}
	}

	n, err := strconv.Atoi(os.Args[len(os.Args)-2])
	if n >= 5000 {
		fmt.Println(RED + "Too many routines, number greater than 5000 may cause lack of port" + RESET)
	}
	if err != nil {
		fmt.Println("Please input a number")
	}

	url := os.Args[len(os.Args)-1]
	for i := 0; i <= n; i++ {
		go CC(url, i, ch)
	}

	var code int
	var newResp = 0
	var okResp = 0
	var errReq = 0
	var badReq = 0
	var speedQueueLen = 32
	var speedQueueTickerInterval = 200
	var speedQueueTicker = time.NewTicker(time.Millisecond * time.Duration(speedQueueTickerInterval))

	var totalReq = 0
	var totalBadReq = 0
	var totalOKReq = 0
	var totalErrorReq = 0

	var speedQueue = make([]struct {
		t       int64
		newResp int
		badReq  int
		errReq  int
	}, 0, speedQueueLen)
	var speedIndex = 0
	for {
		select {
		case <-speedQueueTicker.C:
			var speedItem = struct {
				t       int64
				newResp int
				badReq  int
				errReq  int
			}{
				time.Now().UnixMilli(), newResp, badReq, errReq,
			}
			if len(speedQueue) < speedQueueLen {
				speedQueue = append(speedQueue, speedItem)
				newResp = 0
				errReq = 0
				badReq = 0
				break
			}
			speedQueue[speedIndex] = speedItem

			var interval = speedQueue[speedIndex].t - speedQueue[(speedIndex+1)%speedQueueLen].t
			var concurrency float64 = 0
			var errorRate float64 = 0
			var badRate float64 = 0

			for i := 0; i < speedQueueLen; i++ {
				//fmt.Printf("%d %d %d %d\n", speedQueue[i].t, speedQueue[i].newResp, speedQueue[i].badReq, speedQueue[i].errReq)
				concurrency += float64(speedQueue[i].newResp) / float64(interval) * 1000
				errorRate += float64(speedQueue[i].errReq) / float64(interval) * 1000
				badRate += float64(speedQueue[i].badReq) / float64(interval) * 1000
			}

			fmt.Printf("totalReq: "+BLUE+"%d"+RESET, totalReq)
			fmt.Printf(", totalOKReq: "+BLUE+"%d"+RESET, totalOKReq)
			fmt.Printf(", totalBadReq: "+BLUE+"%d"+RESET, totalBadReq)
			fmt.Printf(", totalErrorReq: "+BLUE+"%d"+RESET, totalErrorReq)
			fmt.Printf(", totalErrorReq: "+BLUE+"%d\n"+RESET, totalErrorReq)
			fmt.Printf("concurrency: "+BLUE+"%f"+RESET, concurrency)
			fmt.Printf(", bad_rate: "+BLUE+"%f"+RESET, badRate)
			fmt.Printf(", error_rate: "+BLUE+"%f"+RESET, errorRate)
			fmt.Printf(", interval: "+BLUE+"%f\n"+RESET, float64(interval)/1000)
			newResp = 0
			errReq = 0
			badReq = 0

			speedIndex = (speedIndex + 1) % speedQueueLen
		case code = <-ch:
			if code == 200 {
				newResp++
				okResp++
				totalOKReq++
				totalReq++
			} else if code == 0 {
				errReq++
				totalErrorReq++
			} else {
				newResp++
				badReq++
				totalBadReq++
				totalReq++
			}
		}
	}
}
